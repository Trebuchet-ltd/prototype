import django_filters
from django.contrib.auth.models import User
from rest_framework import viewsets, status, filters
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponseRedirect
import requests
from requests.auth import HTTPBasicAuth
import datetime
from authentication.permissions import IsOwner
from home.serializers import *
from .models import *
import prototype.settings as settings
from django.contrib.gis.geos import GEOSGeometry


class ProductViewSet(viewsets.ModelViewSet):
    """
    API end point to get all product details
    """
    queryset = Product.objects.all()
    serializer_class = GetProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['bestSeller', 'meat']
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend]
    search_fields = ['title', 'short_description', 'description', 'can_be_cleaned', 'weight_variants']


class CartItemViewSets(viewsets.ModelViewSet):
    """
    Api end point to get cart items
    """
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'post', 'delete']

    def perform_create(self, serializer):
        # The request user is set as author automatically.
        if self.request.user.cart:
            item = self.request.data['item']
            weight_variants = self.request.data['weight_variants']
            is_cleaned = self.request.data['is_cleaned']
            items = self.request.user.cart.items.all().filter(item__id=item, is_cleaned=is_cleaned,
                                                              weight_variants=weight_variants).first()
            if items:
                items.quantity += self.request.data['quantity']
                items.save()
            else:
                serializer.save(cart=self.request.user.cart, item_id=item)


def is_availabe_district(pincode):
    try:
        district = requests.get(f'https://api.postalpincode.in/pincode/{pincode}').json()[0].get("PostOffice")[
            0].get("District")
        print(district)
        # district obj contains the district if it is added to database else return null queryset
        district_obj = District.objects.filter(district_name=district)

        # this check whether the the district added to the database and it is available for delivery
        if not (district_obj and district_obj[0].Available_status):
            return False
    except TypeError:
        pass
    else:
        return True


@api_view(['GET'])
def available_pin_codes(request):
    """ A End point to know the availability of a district """

    pincode = request.GET["pincode"]
    if is_availabe_district(pincode):
        return Response(status=200)
    else:
        return Response({"error": "Delivery to this address is not available"},status=status.HTTP_406_NOT_ACCEPTABLE)


def add_points(token):
    """ Function to add points to user when first purchase occurs """

    if not Tokens.objects.get(invite_token=token).first_purchase_done:
        invite_token = Tokens.objects.get(private_token=token)
        invite_token.points += 10
        invite_token.save()
        return True

    return False


def new_id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """ This function generate a random string  """

    return ''.join(random.choice(chars) for _ in range(size))


def create_new_unique_id():
    """ This function verify the uniqueness of an id for transaction """

    not_unique = True
    unique_id = new_id_generator()
    while not_unique:
        unique_id = new_id_generator()
        if not TransactionDetails.objects.filter(transaction_id=unique_id):
            not_unique = False
    return str(unique_id)


def get_payment_link(user,date,time,amount,address_obj):
    """ This Function returns thr payment url for that particular checkout """

    key_secret = settings.razorpay_key_secret
    call_back_url = settings.webhook_call_back_url
    key_id = settings.razorpay_key_id
    transaction_id = create_new_unique_id()
    transaction_details = TransactionDetails(transaction_id=transaction_id, user=user,
                                             date=date, time=time, address_id=address_obj.id, total=amount)
    transaction_details.save()
    amount *= 100  # converting rupees to paisa
    try:
        url = 'https://api.razorpay.com/v1/payment_links'

        data = {
            "amount": amount,
            "currency": "INR",
            "callback_url": call_back_url,
            "callback_method": "get",
            'reference_id': transaction_id,
            "customer": {
                "contact": address_obj.phone,
                "email": user.email,
                "name": address_obj.name
            },
            "options": {
                "checkout": {
                    "name": "DreamEat",
                    "prefill": {
                        "email": user.email,
                        "contact": address_obj.phone
                    },
                    "readonly": {
                        "email": True,
                        "contact": True
                    }
                }
            }

        }
        x = requests.post(url,
                          json=data,
                          headers={'Content-type': 'application/json'},
                          auth=HTTPBasicAuth(key_id, key_secret))
        data = x.json()
        transaction_details.payment_id = data.get("id")
        transaction_details.payment_status = data.get("status")
        transaction_details.save()
        payment_url = data.get('short_url')
        return payment_url
    except Exception as e:
        print(e)
        return False


def is_valid_date(date_obj, time):
    """ This function check the user selected date and time is valid or not """

    if (date_obj.date() - datetime.datetime.now().date()).days < 0:
        return False
    elif date_obj.date() == datetime.datetime.now().date():  # checking the date is today or not
        if time == "morning":  # if the date is today morning slot is not available
            return False
    return True


def is_out_of_stock(user):
    """ This function checks the stock availability of the product """
    for item in user.cart.items.all():
        reduction_in_stock = item.weight_variants * item.quantity / 1000
        if item.item.stock - reduction_in_stock <= 0:

            return item.item
    return False


def total_amount(user,address_obj):
    """ This function returns the total amount of the cart items of the user """

    cart = user.cart
    amount = 0

    for item in cart.items.all():
        if item.quantity > 0:
            if item.is_cleaned:
                amount += item.quantity * item.item.cleaned_price * item.weight_variants / 1000
            else:
                amount += item.quantity * item.item.price * item.weight_variants / 1000

        elif item.quantity < 0:
            if item.is_cleaned:
                amount += -item.quantity * item.item.cleaned_price * item.weight_variants / 1000
            else:
                amount += -item.quantity * item.item.price * item.weight_variants / 1000

    if amount < 500:
        amount += address_obj.delivery_charge

    return amount


@api_view(["POST"])
def confirm_order(request):

    date = request.data["date"]
    date_str = "".join(date.split("-"))
    time = request.data["time"]
    address = request.data["selected_address"]
    date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')

    # checking the date is not a past date
    if not is_valid_date(date_obj, time):
        return Response({"error": "Date should be a future date"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    # item will false when stock available otherwise this will be thw name of that particular item that is out of stock
    item = is_out_of_stock(request.user)
    if item:
        return Response({"error": f" Item {item} is out of stock"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    address_obj = Addresses.objects.get(id=address)
    if not is_availabe_district(address_obj.pincode):
        return Response({"error": "Delivery to this address is not available"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    user = User.objects.get(id=request.user.id)
    amount = total_amount(user, address_obj)
    if amount > 0:
        payment_url = get_payment_link(user, date, time, amount, address_obj)
        if payment_url:
            return Response({"payment_url": payment_url})
        else:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)


def payment(request):
    if request.method == "GET":
        try:
            transaction_details = TransactionDetails.objects.get(
                transaction_id = request.GET["razorpay_payment_link_reference_id"])
            transaction_details.payment_status = request.GET["razorpay_payment_link_status"]

            user = transaction_details.user
            cart = user.cart

            order = Orders.objects.create(user=user, date=transaction_details.date, time=transaction_details.time[0],
                                          address_id=transaction_details.address_id,
                                          total=transaction_details.total, status="p", )
            order.save()
            transaction_details.order = order
            transaction_details.save()
            token = Tokens.objects.get(user=user)
            if not token.first_purchase_done:
                add_points(token.invite_token)

            for item in cart.items.all():
                order_item = OrderItem.objects.create(item=item.item, quantity=item.quantity, order=order,
                                                      weight_variants=item.weight_variants,
                                                      is_cleaned=item.is_cleaned)
                order_item.save()
                reduction_in_stock = item.weight_variants * item.quantity / 1000
                item.item.stock -= reduction_in_stock
                item.item.save()
                item.delete()
            cart.total = 0
            cart.save()
        except Exception as ex:
            print(ex)
    return HttpResponseRedirect(settings.webhook_redirect_url)


class CartViewSets(viewsets.ModelViewSet):
    """
    Api end point to get cart fully
    """
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = CartModel.objects.all()
    serializer_class = CartSerializer

    def list(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            self.queryset = self.queryset.filter(user=request.user)
        return viewsets.ModelViewSet.list(self, request, *args, **kwargs)

    @action(detail=False, methods=["get", "post", 'delete'], url_path='me')
    def me(self, request, *args, **kwargs):
        self.queryset = self.queryset.filter(user=request.user)
        return viewsets.ModelViewSet.list(self, request, *args, **kwargs)


class OrderViewSets(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Orders.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        self.queryset = Orders.objects.filter(user=self.request.user)
        return self.queryset


def distance_between(loc1, loc2):
    pnt1 = GEOSGeometry(f"POINT ({loc1[0]} {loc1[1]})")
    pnt2 = GEOSGeometry(f"POINT ({loc2[0]} {loc2[1]})")
    distance = pnt1.distance(pnt2)*100
    return distance


def get_delivery_charge(location):
    distance = distance_between(settings.location, [location[0], location[1]])
    if distance <= 10:
        return 30
    else:
        return 60


class AddressViewSets(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Addresses.objects.all()
    serializer_class = GetAddressSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        self.queryset = Addresses.objects.filter(user=self.request.user)

        return self.queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        location = request.data["latitude"], request.data["longitude"]
        delivery_charge = get_delivery_charge(location)
        serializer.initial_data["delivery_charge"] = delivery_charge
        print(serializer.initial_data)
        serializer.is_valid(raise_exception=True)

        serializer.save(user=request.user)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        location = self.request.data["latitude"], self.request.data["longitude"]
        delivery_charge = get_delivery_charge(location)
        print(f"{delivery_charge = }")
        serializer.save(delivery_charge=delivery_charge)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

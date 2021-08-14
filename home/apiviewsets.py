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
from authentication.permissions import IsOwner, IsMyCartItem
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
    permission_classes = [permissions.IsAuthenticated, IsMyCartItem]
    http_method_names = ['get', 'patch', 'post', 'delete']

    def get_queryset(self):
        self.queryset = CartItem.objects.filter(cart=self.request.user.cart)
        if self.queryset:
            return self.queryset
        else:
            self.queryset = CartItem.objects.none()
            return self.queryset

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
    purchase_done = Tokens.objects.get(invite_token=token).first_purchase_done
    if not purchase_done:
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


def create_temp_order(cart, payment_id, date,time,address_obj, coupon_code):
    """
    This will create an intermediate object of order and order items for storing the current cart items ans details

    """

    order = TempOrder.objects.create(payment_id=payment_id, date=date, time=time,
                                     address_id=address_obj.id, coupon=coupon_code)
    order.save()
    for item in cart.items.all():
        temp_item = TempItem.objects.create(item=item.item, quantity=item.quantity, order=order,
                                            weight_variants=item.weight_variants,
                                            is_cleaned=item.is_cleaned)
        temp_item.save()


def get_payment_link(user, date, time, amount, address_obj):
    """
    This Function returns thr payment url for that particular checkout
    Returns a list with payment link and payment id created by razorpay
    """

    key_secret = settings.razorpay_key_secret
    call_back_url = settings.webhook_call_back_url
    key_id = settings.razorpay_key_id
    transaction_id = create_new_unique_id()
    transaction_details = TransactionDetails(transaction_id=transaction_id, user=user, total=amount)
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
        return [payment_url, transaction_details.payment_id]
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


def is_valid_coupon(user, coupon_code, amount):
    """
    This function validates the specified coupon applicable or not
    Returns a list with first element will be the status (boolean) second element is the error if not valid
    Returns [True] if the coupon is valid
    """
    coupon_obj = Coupon.objects.get(code=coupon_code)
    if coupon_code is None:  # checks the coupon is existing one
        return [False, "coupon code does not exist"]
    if coupon_obj.expired:  # check the coupon expired or not
        return [False, "coupon code does not exist"]
    if coupon_obj.user_specific_status:     # checks the coupon is user specific or not
        if coupon_obj.specific_user != user:    # check the specific user is not the requested user
            return [False, "coupon code does not exist"]
    if coupon_obj.minimum_price > amount:   # checks the minimum price condition
        return [False, f"This coupon is applicable to the amount greater than {coupon_obj.minimum_price} "]

    return [True]


def apply_coupon(coupon_code, amount):
    """
    This function apply the coupon code and
    """
    coupon_obj = Coupon.objects.get(code=coupon_code)

# {
# "date":"2021-11-05",
# "time":"morning",
# "selected_address":17
# }


def total_amount(user, address_obj):
    """
    This function returns the total amount of the cart items of the user
    Return 0 if the amount is zero
    return amount + delivery charge if amount less than 500
    return amount if amount more than 500

    """

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
    if amount <= 0:
        return 0

    if amount < 500:
        amount += address_obj.delivery_charge
    return amount


@api_view(["POST"])
def confirm_order(request):

    date = request.data["date"]
    date_str = "".join(date.split("-"))  # converting '2017-05-05' to '20170505'
    time = request.data["time"]
    address = request.data["selected_address"]
    date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')
    coupon_code = ''
    if hasattr(request.data, "coupon_code"):  # if coupon code is applied the coupon_code will be that string
        coupon_code = request.POST["coupon_code"]

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
        [payment_url, payment_id] = get_payment_link(user, date, time, amount, address_obj)
        if payment_url:
            # creating a temporary order for saving the current details of cart
            create_temp_order(user.cart, payment_id, date, time, address_obj, coupon_code)

            return Response({"payment_url": payment_url})
        else:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        return Response({"error": "total amount must be positive "}, status=status.HTTP_406_NOT_ACCEPTABLE)


def create_order_items(cart, temp_items, order):

    for item in temp_items.all():
        order_item = OrderItem.objects.create(item=item.item, quantity=item.quantity, order=order,
                                              weight_variants=item.weight_variants,
                                              is_cleaned=item.is_cleaned)
        order_item.save()
        reduction_in_stock = item.weight_variants * item.quantity / 1000
        item.item.stock -= reduction_in_stock
        item.item.save()
        CartItem.objects.filter(item=item.item, weight_variants=item.weight_variants,
                                is_cleaned=item.is_cleaned).delete()

    cart.total = 0
    cart.save()


@api_view()
def payment(request):
    if request.method == "GET":
        try:
            transaction_details = TransactionDetails.objects.get(
                transaction_id=request.GET["razorpay_payment_link_reference_id"])
            transaction_details.payment_status = request.GET["razorpay_payment_link_status"]

            #   temp order will have the intermediate  order details between checkout and payment
            #   the items added after checkout will not be in temp order

            temp_order = TempOrder.objects.get(payment_id=transaction_details.payment_id)
            temp_items = TempItem.objects.filter(order=temp_order)
            user = transaction_details.user
            cart = user.cart

            order = Orders.objects.create(user=user, date=temp_order.date, time=temp_order.time[0],
                                          address_id=temp_order.address_id,
                                          total=transaction_details.total, status="p", )
            order.save()
            transaction_details.order = order
            transaction_details.save()
            token = Tokens.objects.get(user=user)
            if not token.first_purchase_done:
                if token.invite_token:  # All user may not be invite token that's why this check is here
                    add_points(token.invite_token)  # Thi function add points if token is valid
                    token.first_purchase_done = True    # after first purchase this will executed and make is True
                    token.save()

            create_order_items(cart, temp_items, order)

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
    http_method_names = ['get']

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

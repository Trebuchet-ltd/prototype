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
from math import sin, cos, sqrt, atan2, radians
from authentication.permissions import IsOwner
from home.serializers import *
from .models import *
import prototype.settings as settings


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


@api_view(['GET'])
def available_pin_codes(request):
    pincode = request.GET["pincode"]
    try:

        district = requests.get(f'https://api.postalpincode.in/pincode/{pincode}').json()[0].get("PostOffice")[
            0].get("District")
        print(district)
        # district obj contains the district if it is added to database else return null queryset
        district_obj = District.objects.filter(district_name=district)

        # this check whether the the district added to the database and it is available for delivery
        if not (district_obj and district_obj[0].Available_status):
            return Response({"error": "Delivery to this address is not available"})
        else:
            return Response(status=200)

    except Exception as e:
        print(e)
        return Response(status=400)


@api_view(["POST"])
def confirm_order(request):

    date = request.data["date"]
    date_str = "".join(date.split("-"))
    time = request.data["time"]
    address = request.data["selected_address"]
    key_id = settings.razorpay_key_id
    date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')

    # checking the date is not a past date
    if date_obj.day - datetime.datetime.now().day < 0:
        return Response({"error": "Date should be a future date"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    elif date_obj.day == datetime.datetime.now().day:  # checking the date is today or not
        if time == "morning":  # if the date is today morning slot is not available
            return Response({"error": "Time should be a future time"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    for item in request.user.cart.items.all():
        reduction_in_stock = item.weight_variants * item.quantity / 1000
        if item.item.stock - reduction_in_stock <= 0:
            return Response({"error": f" Item {item.item} is out of stock"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    try:
        address_obj = Addresses.objects.get(id=address)
        # get the district of the pincode of user from the indian postal api
        # It returns a object that include the array of post offices in that pincode and it include the district
        district = requests.get(f'https://api.postalpincode.in/pincode/{address_obj.pincode}')\
            .json()[0].get("PostOffice")[0].get("District")

        # district obj contains the district if it is added to database else return null queryset
        district_obj = District.objects.filter(district_name=district)

        # this check whether the the district added to the database and it is available for delivery
        if not (district_obj and district_obj[0].Available_status):
            return Response({"error": "Delivery to this address is not available"})

    except Exception as e:
        print(e)
        return Response({"error": "Invalid pincode "}, status=status.HTTP_406_NOT_ACCEPTABLE)

    key_secret = settings.razorpay_key_secret
    call_back_url = settings.webhook_call_back_url

    def new_id_generator(size=6, chars=string.ascii_uppercase + string.digits):

        """ This function generate a random string  """
        return ''.join(random.choice(chars) for _ in range(size))

    def create_new_unique_id():
        """ This function verify the id for transaction """
        not_unique = True
        unique_id = new_id_generator()
        while not_unique:
            unique_id = new_id_generator()
            if not TransactionDetails.objects.filter(transaction_id=unique_id):
                not_unique = False
        return str(unique_id)

    try:
        user = User.objects.get(id=request.user.id)
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

        if amount > 0:

            transaction_id = create_new_unique_id()
            transaction_details = TransactionDetails(transaction_id=transaction_id, user=user,
                                                     date=date, time=time, address_id=address, total=amount)
            transaction_details.save()
            amount *= 100  # converting rupees to paisa

            try:
                url = 'https://api.razorpay.com/v1/payment_links'
                my_obj = {
                    "amount": amount,
                    "currency": "INR",
                    "callback_url": call_back_url,
                    "callback_method": "get",
                    'reference_id': transaction_id,
                    "customer": {
                        "contact": address_obj.phone,
                        "email": user.email,
                        "name": user.username
                    },

                }
                x = requests.post(url,
                                  json=my_obj,
                                  headers={'Content-type': 'application/json'},
                                  auth=HTTPBasicAuth(key_id, key_secret))
                data = x.json()

                transaction_details.payment_id = data.get("id")
                transaction_details.payment_status = data.get("status")
                transaction_details.save()
                payment_url = data.get('short_url')
                return Response({"payment_url": payment_url})
            except Exception as e:
                print(e)
                Response(status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        print(e)
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE)


def payment(request):
    if request.method == "GET":
        try:
            transaction_details = TransactionDetails.objects.get(
                transaction_id=request.GET["razorpay_payment_link_reference_id"])
            transaction_details.payment_status = request.GET["razorpay_payment_link_status"]

            user = transaction_details.user
            cart = user.cart

            order = Orders.objects.create(user=user, date=transaction_details.date, time=transaction_details.time[0],
                                          address_id=transaction_details.address_id,
                                          total=transaction_details.total, status="p", )
            order.save()
            transaction_details.order = order
            transaction_details.save()
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

    earth_radius = 6373.0
    lat1 = radians(loc1[0])
    lon1 = radians(loc1[1])
    lat2 = radians(loc2[0])
    lon2 = radians(loc2[1])

    dif_lon = lon2 - lon1
    dif_lat = lat2 - lat1

    a = sin(dif_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dif_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = earth_radius * c
    return distance


def get_delivery_charge(location):
    distance = distance_between(settings.location, [location[0], location[1]])
    if distance <= 15:
        return 30
    else:
        return 60


class AddressViewSets(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Addresses.objects.all()
    serializer_class = GetAddressSerializer
    http_method_names = ['get', 'post', 'patch']

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

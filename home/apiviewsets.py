import django_filters
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, status, filters
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from home.serializers import *
from .models import *
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt
import os
import requests
import razorpay
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
    serializer_class = getProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['bestSeller', 'meat']
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend]
    search_fields = ['title', 'short_description','description','can_be_cleaned','weight_variants']
    # @action(methods=['get'], detail=False, permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    # def front_page(self, request):
    #     best_sellers = Product.objects.all().filter(bestSeller=True)
    #     fish = Product.objects.all().filter(meat='f')
    #     meat = Product.objects.all().filter(meat='m')
    #
    #     page = self.paginate_queryset()
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(best_sellers, many=True)


class CartItemViewSets(viewsets.ModelViewSet):
    """
    Api end point to get cart items
    """
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get','patch','post']
    def perform_create(self, serializer):
        # The request user is set as author automatically.
        if self.request.user.cart:
            item = self.request.data['item']
            items = self.request.user.cart.items.all().filter(item__id=item).first()
            if items:
                items.quantity+=self.request.data['quantity']
                items.save()
            else:
                serializer.save(cart=self.request.user.cart,item_id=item)

    def perform_update(self, serializer):
        if self.request.user.cart:
            item = self.request.data["item"]
            items = self.request.user.cart.items.all().filter(item__id=item).first()
            if items:
                print(self.request.data['quantity'])
                items.quantity = self.request.data['quantity']
                items.save()

    #transaction/?date=2021-8-2&time="morning"&selected_address=1

@api_view(['GET'])
def availablePincodes(request):
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
def confirmOrder(request):
    global paymenturl

    date = request.data["date"]
    date_str = "".join(date.split("-"))
    time = request.data["time"]
    address = request.data["selected_address"]
    key_id = settings.razorpay_key_id
    date_obj = datetime.datetime.strptime(date_str,'%Y%m%d')

    # checking weather the date is a future date by calculating differance between today and date from request
    # if (date_obj-datetime.datetime.now()).days < 1:
    #     return  Response({"error":"Date should be a future date"},status=400)
    address_obj = Addresses.objects.get(id=int(address))

    # checking the date is not a past date
    if date_obj.day - datetime.datetime.now().day < 0:
        return Response({"error": "Date should be a future date"}, status=400)
    elif date_obj.day == datetime.datetime.now().day:   # checking the date is today or not
        if time == "morning": # if the date is today morning slot is not available
            return Response({"error": "Time should be a future time"}, status=400)
    for item in request.user.cart.items.all():
        reduction_in_stock = item.weight_variants * item.quantity / 1000
        if item.item.stock - reduction_in_stock <= 0:
            return Response({"error": f" Item {item.item} is out of stock"}, status=400)



    # get the district of the pincode of user from the indian postal api
    # It returns a object that include the array of post offices in that pincode and it include the district
    # print(f"{request.user.cart.item.stock}")
    district = requests.get(f'https://api.postalpincode.in/pincode/{address_obj.pincode}').json()[0].get("PostOffice")[0].get("District")
    # district obj contains the district if it is added to database else return null queryset
    district_obj = District.objects.filter(district_name=district)

    # this check whether the the district added to the database and it is available for delivery
    if not (district_obj and district_obj[0].Available_status):
        return Response({"error": "Delivery to this address is not available"})

    key_secret = settings.razorpay_key_secret
    call_back_url = settings.webhook_call_back_url

    def id_generator(size=6, chars = string.ascii_uppercase + string.digits):

        """ This function generate a random string  """
        return ''.join(random.choice(chars) for _ in range(size))

    def create_new_id():
        """ This function veryfy the id for transaction """
        not_unique = True
        unique_id = id_generator()
        while not_unique:
            unique_id = id_generator()
            if not TransactionDetails.objects.filter(transaction_id=unique_id):
                not_unique = False
        return str(unique_id)

    try:
        user = User.objects.get(id=request.user.id)
        cart = user.cart
        amount = 0

        for item in cart.items.all():
            if item.quantity > 0 :
                if item.can_be_cleaned:
                    amount += item.quantity * item.item.cleaned_price * item.weight_variants / 1000
                else:
                    amount += item.quantity * item.item.prize * item.weight_variants / 1000

            elif item.quantity < 0:
                if item.can_be_cleaned:
                    amount += -item.quantity * item.item.cleaned_price * item.weight_variants / 1000
                else:
                    amount += -item.quantity * item.item.prize * item.weight_variants / 1000

        amount += address_obj.delivery_charge

        print(f"{amount = }")

        if amount > 0:

            transaction_id = create_new_id()
            transactionDetails = TransactionDetails(transaction_id=transaction_id, user=user,
                                                    date=date, time=time, adress_id=address,total=amount)
            transactionDetails.save()
            amount *= 100  # converting rupees to paisa
            DATA = {
                "amount": amount,
                "currency": "INR",
                "receipt": transaction_id
                }
            client = razorpay.Client(auth=(key_id, key_secret))
            client.set_app_details({"title": "Prototype", "version": "1"})

            try:
                order = client.order.create(data=DATA)
                url = 'https://api.razorpay.com/v1/payment_links'

                myobj = {
                    "amount": amount,
                    "currency": "INR",
                    "callback_url": call_back_url,
                    "callback_method": "get",
                    'reference_id': transaction_id
                    }
                x = requests.post(url,
                                  json=myobj,
                                  headers={'Content-type': 'application/json'},
                                  auth=HTTPBasicAuth(key_id, key_secret))
                data = x.json()

                transactionDetails.payment_id = data.get("id")
                transactionDetails.payment_status = data.get("status")
                transactionDetails.save()
                paymenturl = data.get('short_url')
                return Response({"payment_url": paymenturl})
            except Exception as e:
                print(e)
                Response(status=400)
    except Exception as e:
        print(e)
        return Response(status=400)


def payment(request):
    if request.method == "GET":
        try:
            transactiondetails = TransactionDetails.objects.get(transaction_id=request.GET["razorpay_payment_link_reference_id"])
            transactiondetails.payment_status=request.GET["razorpay_payment_link_status"]

            user = transactiondetails.user
            cart = user.cart

            order = Orders.objects.create(user=user, date=transactiondetails.date, time=transactiondetails.time[0],
                                          address_id=transactiondetails.adress_id,
                                          total=transactiondetails.total, status="p",)
            order.save()
            transactiondetails.order = order
            transactiondetails.save()
            for item in cart.items.all():
                order_item = OrderItem.objects.create(item=item.item, quantity=item.quantity, order=order
                                                      ,weight_variants=item.weight_variants,can_be_cleaned=item.can_be_cleaned )
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


class AddressViewSets(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Addresses.objects.all()
    serializer_class = GetAddressSerializer
    http_method_names = ['get', 'post','patch']
    def get_queryset(self):
        self.queryset = Addresses.objects.filter(user=self.request.user)

        return self.queryset

    def distance_btwn(self,loc1,loc2):
        R = 6373.0

        lat1 = radians(loc1[0])
        lon1 = radians(loc1[1])
        lat2 = radians(loc2[0])
        lon2 = radians(loc2[1])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        return round(distance)
    def delivery_charge(self,location):
        distance = self.distance_btwn([9.997795804491675, 76.26409019445995],[location[0],location[1]])
        if distance <= 15:
            return 30
        else:
            return 60

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        location = request.data["latitude"], request.data["longitude"]
        delivery_charge = self.delivery_charge(location)

        serializer.initial_data["delivery_charge"] = delivery_charge
        print(serializer.initial_data)
        serializer.is_valid(raise_exception=True    )

        serializer.save(user=request.user)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)





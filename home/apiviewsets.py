from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from home.serializers import *
from .models import *
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import requests
import razorpay
from requests.auth import HTTPBasicAuth


from authentication.permissions import IsOwner
from home.serializers import *
from .models import *



class ProductViewSet(viewsets.ModelViewSet):
    """
    API end point to get all product details
    """
    queryset = Product.objects.all()
    serializer_class = getProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['bestSeller', 'meat']

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

@api_view()
def confirm_order(request):
    # transaction/?date=25-07-2021&time=morning&address=1
    print(request.user)
    date = request.GET['date']
    time = request.GET['time']
    address =request.GET['address']


    key_id = config("key_id")
    key_secret = config("key_secret")

    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        """ This function generate a random string  """
        return ''.join(random.choice(chars) for _ in range(size))

    def create_new_id():
        """ This function create an unique id for transaction """
        not_unique = True
        unique_id = id_generator()
        while not_unique:
            unique_id = id_generator()
            if not TransactionDetails.objects.filter(transation_id=unique_id):
                not_unique = False
        return str(unique_id)
    try:
        # call back url to payment link
        call_back_url ='https://0c9c5151a1b5.ngrok.io/payment'
        user = User.objects.get(id=request.user.id)

        cart = user.cart
        try:
            order = Orders.objects.create(user=request.user, date=date, time=time, address_id=int(address),
                                          total=cart.total)
            order.save()
        except Exception as e:
            print(f"ex {e}")




        amount = 0
        for item in cart.items.all():
            if item.quantity > 0:
                amount += item.quantity * item.item.price
            elif item.quantity < 0:
                amount += -item.quantity * item.item.price
            order_item = OrderItem.objects.create(item=item.item, quantity=item.quantity, order=order)
            order_item.save()
        print(amount)
        amount *= 100  # converting rupees to paisa

        if amount > 0:
            transaction_id = create_new_id()
            transactionDetails = TransactionDetails(transation_id=transaction_id, user=user)
            transactionDetails.save()
            DATA = {
                "amount": amount,
                "currency": "INR",
                "receipt": transaction_id
            }
            client = razorpay.Client(auth=(key_id, key_secret))
            client.set_app_details({"title": "CARBLE", "version": "1"})
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
        else:
            Response({"Error": "The total amount cannot be negative"})
    except Exception as e:
        print(e)

    return Response(status=400)


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

    @action(detail=False, methods=["get", "post"], url_path='me')
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






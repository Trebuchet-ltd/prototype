import django_filters
from django.contrib.auth.models import User
from rest_framework import viewsets, status, filters
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from authentication.permissions import IsOwner, IsMyCartItem
from home.serializers import *
from .functions import *
import logging


class ProductViewSet(viewsets.ModelViewSet):
    """
    API end point to get all product details
    """
    http_method_names = ['get']
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


@api_view(['GET'])
def available_pin_codes(request):
    """ A End point to know the availability of a district  """

    pincode = request.GET["pincode"]
    if not pincode.isdigit() or len(pincode) != 6:
        return Response({"error": "Delivery to this address is not available"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    if is_available_district(pincode):
        return Response(status=200)
    else:
        return Response({"error": "Delivery to this address is not available"}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
def get_coupon(request):
    """
    {
    "coupon_code":"<code>",
    "selected_address":id
    }
    """
    user = request.user
    coupon_code = request.data["coupon_code"]
    address = request.data["selected_address"]
    logging.info(f"{request.user} checking for coupon request data ={request.data} ")
    address_obj = Addresses.objects.filter(id=address, user=request.user).first()
    logging.info(f"address_obj is {address_obj} ")
    if not address_obj:
        logging.info(f"User requested address is not exist for {request.user} ")
        return Response({"error": "Delivery  address not available"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    amount = total_amount(user, address_obj, coupon_code, without_coupon=True)
    coupon_status = is_valid_coupon(user, coupon_code, amount)
    print(f"{amount = }")
    if coupon_status[0]:
        discount = amount - apply_coupon(user, coupon_code, amount)
        return Response({"discount": discount}, status=status.HTTP_202_ACCEPTED)
    else:
        return Response({"error": coupon_status[1]}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
def confirm_order(request):
    """
    {
    "date":"2021-11-05",
    "time":"evening",
    "selected_address":id,
    "coupon_code":"<code>",
    "points":num

    }
    """

    date = request.data["date"]
    date_str = "".join(date.split("-"))  # converting '2017-05-05' to '20170505'
    time = request.data["time"]
    address = request.data["selected_address"]
    date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')
    coupon_code = request.data.get("coupon_code")
    points = request.data.get("points")
    logging.info(f"{request.user.username} requested for checkout ... ")
    logging.info(f"requested data {request.data} ")
    # checking the date is not a past date
    if not is_valid_date(date_obj, time):
        logging.info(f"checkout cancelled because of invalid date for user {request.user} ")
        return Response({"error": "Date should be a future date"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    # item will false when stock available otherwise this will be thw name of that particular item that is out of stock
    item = is_out_of_stock(request.user)
    if item:
        logging.info("Request not accepted due to out of stock")
        return Response({"error": f" Item {item} is out of stock"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    address_obj = Addresses.objects.filter(id=address, user=request.user).first()
    logging.info(f"address_obj is {address_obj} ")
    if not address_obj:
        logging.info(f"User requested address is not exist for {request.user} ")
        return Response({"error": "Delivery  address not available"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    if not is_available_district(address_obj.pincode):
        logging.info("Request not accepted because pincode is not available ")
        return Response({"error": "Delivery to this address is not available"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    user = request.user

    amount = total_amount(user, address_obj, coupon_code, points)

    logging.info(f"Total amount = {amount} ")
    if amount > 0:
        [payment_url, payment_id] = get_payment_link(user, amount, address_obj)
        if payment_url:
            # creating a temporary order for saving the current details of cart
            create_temp_order(user, payment_id, date, time, address_obj, coupon_code, points)
            logging.info("sent the payment link successfully")
            return Response({"payment_url": payment_url})
        else:
            logging.warning("payment link not sent")
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        logging.info("Cart is empty request canceled ")
        return Response({"error": "Cart is empty "}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
def payment(request):
    print(request)
    logging.info("Webhook from razorpay called ...")
    if verify_signature(request):
        try:
            transaction_details = TransactionDetails.objects.get(
                transaction_id=request.GET["razorpay_payment_link_reference_id"])
            transaction_details.payment_status = request.GET["razorpay_payment_link_status"]
            logging.info(f"payment status {transaction_details.payment_status}")
            #   temp order will have the intermediate  order details between checkout and payment
            #   the items added after checkout will not be in temp order
            logging.info("collecting data  from temporary order ")
            temp_order = TempOrder.objects.get(payment_id=transaction_details.payment_id)
            temp_items = TempItem.objects.filter(order=temp_order)
            user = transaction_details.user
            logging.info(f"user - {user.username}")
            cart = user.cart
            if temp_order.coupon:
                logging.info(f"Payment done by using coupon {temp_order.coupon.code}")
                order = Orders.objects.create(user=user, date=temp_order.date, time=temp_order.time[0],
                                              address_id=temp_order.address_id,
                                              total=transaction_details.total,
                                              status="p", coupon=temp_order.coupon, used_points=temp_order.used_points)
            else:
                order = Orders.objects.create(user=user, date=temp_order.date, time=temp_order.time[0],
                                              address_id=temp_order.address_id,
                                              total=transaction_details.total, status="p",
                                              used_points=temp_order.used_points)
            logging.info("creating order ")
            order.save()
            if order.used_points:
                reduce_points(user)
            transaction_details.order = order
            transaction_details.save()
            token = user.tokens
            if not token.first_purchase_done:
                logging.info("first purchase ")
                if token.invite_token:  # All user may not be invite token that's why this check is here
                    logging.info(f"{user.name} is invited by {token.invite_token} token")
                    add_points(token.invite_token)  # This function add points if token is valid
                token.first_purchase_done = True  # after first purchase this will executed and make is True
                token.save()

            create_order_items(cart, temp_items, order)
            temp_order.delete()
            logging.info("order creation completed")
        except TempOrder.DoesNotExist:
            logging.warning("Temporary order does not exist  already created an order from this")
        except Exception as ex:
            logging.warning(f"order not created exception {ex} ")
    else:
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
    return HttpResponseRedirect(settings.webhook_redirect_url)


class CartViewSets(viewsets.ModelViewSet):
    """
    Api end point to get cart fully
    """
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = CartModel.objects.all()
    serializer_class = CartSerializer
    http_method_names = ['get']

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
    http_method_names = ['get']

    def get_queryset(self):
        self.queryset = Orders.objects.filter(user=self.request.user)
        return self.queryset


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

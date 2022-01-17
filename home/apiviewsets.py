import django_filters
from django.db.models import Q
from django.http import HttpResponseRedirect
from rest_framework import permissions
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework.response import Response

from authentication.permissions import IsOwner, IsMyCartItem
from billing.utils import invoice_data_processor
from home.serializers import *
from .functions import *


class ProductViewSet(viewsets.ModelViewSet):
    """
    API end point to get all product details
    """
    http_method_names = ['get']
    queryset = Product.objects.all()
    serializer_class = GetProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['bestSeller', 'meat', 'meat__category', "meat__code", 'code']
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend]
    search_fields = ['title', 'short_description', 'description', 'can_be_cleaned', 'weight_variants']

    @action(detail=False, methods=["get", ], url_path='offers')
    def offers(self, request, *args, **kwargs):
        products = Product.objects.filter(~Q(discount=0))
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(products, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=["get", ], url_path='code')
    def code(self, request, *args, **kwargs):
        try:

            ret = Product.objects.get(code__iexact=request.GET['code'])
            serializer = self.get_serializer(ret)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response(status=400)


class RecipeBoxViewSet(viewsets.ModelViewSet):
    """
    API end point to get all Recipe Box details
    """
    http_method_names = ['get']
    queryset = RecipeBox.objects.all()
    serializer_class = GetRecipeBoxSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend]
    search_fields = ['title', 'description', ]


class CategoryViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    queryset = Category.objects.all()
    serializer_class = GetCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['category', 'code']
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend]


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API end point to get reviews and write reviews
    """
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Reviews.objects.all()
    serializer_class = GetReviewSerializer
    permission_classes = [IsOwner]
    filterset_fields = ['item']
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend]

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.request.method == 'PATCH':
            serializer_class = GetReviewSerializerWithoutUser

        return serializer_class

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        user = request.user
        item = request.data["item"]

        logger.info(f"{user} requested to write review for product {item}")
        valid, err = is_valid_review(user, item)
        if not valid:
            return Response({"error": err}, status=status.HTTP_406_NOT_ACCEPTABLE)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
    logger.info(f"{request.user} checking for coupon request data ={request.data} ")
    address_obj = Addresses.objects.filter(id=address, user=request.user).first()
    logger.info(f"address_obj is {address_obj} ")
    if not address_obj:
        logger.info(f"User requested address is not exist for {request.user} ")
        return Response({"error": "Delivery  address not available"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    amount, actual_amount = total_amount(user, address_obj, coupon_code, without_coupon=True)
    coupon_status = is_valid_coupon(user, coupon_code, amount)
    logger.info(amount)
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
    user = request.user

    date = request.data["date"]
    date_str = "".join(date.split("-"))  # converting '2017-05-05' to '20170505'
    time = request.data["time"]
    address = request.data["selected_address"]
    date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')
    coupon_code = request.data.get("coupon_code")
    points = request.data.get("points")
    logger.info(f"{request.user.username} requested for checkout ... ")
    logger.info(f"requested data {request.data} ")
    # checking the date is not a past date
    if not is_valid_date(date_obj, time):
        logger.info(f"checkout cancelled because of invalid date for user {request.user} ")
        return Response({"error": "Date should be a future date"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    # item will false when stock available otherwise this will be thw name of that particular item that is out of stock
    item = is_out_of_stock(request.user)
    if item:
        logger.info("Request not accepted due to out of stock")
        return Response({"error": f" Item {item} is out of stock"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    address_obj = Addresses.objects.filter(id=address, user=request.user).first()
    logger.info(f"address_obj is {address_obj} ")
    if not address_obj:
        logger.info(f"User requested address is not exist for {request.user} ")
        return Response({"error": "Delivery  address not available"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    if not is_available_district(address_obj.pincode):
        logger.info("Request not accepted because pincode is not available ")
        return Response({"error": "Delivery to this address is not available"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    amount, actual_amount = total_amount(user, address_obj, coupon_code, points)
    amount_saved = actual_amount - amount

    logger.info(f"Total amount = {amount} amount saved = {amount_saved} ")
    if amount > 0:
        [payment_url, payment_id] = get_payment_link(user, amount, amount_saved, address_obj)
        if payment_url:
            # creating a temporary order for saving the current details of cart
            create_temp_order(user, payment_id, date, time, address_obj, coupon_code, points)
            logger.info("sent the payment link successfully")
            return Response({"payment_url": payment_url})
        else:
            logger.warning("payment link not sent")
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        logger.info("Cart is empty request canceled ")
        return Response({"error": "Cart is empty "}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
def payment(request):
    print(request)
    logger.info("Webhook from razorpay called ...")
    if verify_signature(request):
        transaction_id = request.GET["razorpay_payment_link_reference_id"]
        payment_status = request.GET["razorpay_payment_link_status"]
        handle_payment(transaction_id, payment_status)
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
    permission_classes = [permissions.IsAdminUser]
    queryset = Orders.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Orders.objects.all()

        return Orders.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path='order')
    def order(self, request, *args, **kwargs):
        invoice_data = request.data

        order = invoice_data_processor(invoice_data, request.user.tokens.organisation)

        serializer = self.get_serializer(order, many=False)
        return Response(serializer.data, status=200)


class PurchaseViewSets(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = Orders.objects.all()
    serializer_class = PurchaseSerializer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Orders.objects.all()

        return Orders.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path='order')
    def order(self, request, *args, **kwargs):
        order = invoice_data_processor(request.data)

        serializer = self.get_serializer(order, many=False)
        return Response(serializer.data, status=200)


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

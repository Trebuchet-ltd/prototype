import datetime
import json

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response

from home.models import Orders, OrderItem, Purchase
from home.serializers import OrderSerializer
from .forms import ProductForm
from .models import HsnCode, BillingProduct
from .serializers import HSNSerializer, BillingProductSerializer
from .utils import invoice_data_processor, product_data_processor


def test(user):
    return True if user.tokens.organisation else False


def login_view(request):
    if request.user.is_authenticated:
        return redirect("invoice_create")
    context = {}
    auth_form = AuthenticationForm(request)
    if request.method == "POST":
        auth_form = AuthenticationForm(request, data=request.POST)
        if auth_form.is_valid():
            user = auth_form.get_user()
            if user:
                login(request, user)
                return redirect("invoice_create")
        else:
            context["error_message"] = auth_form.get_invalid_login_error()
    context["auth_form"] = auth_form
    return render(request, 'gstbillingapp/login.html', context)


def refactor(request, function, model, org):
    context = {}
    last_order = model.objects.all().order_by('-id').first()
    if last_order:
        context['default_invoice_number'] = last_order.id + 1
    else:
        context['default_invoice_number'] = 1

    context['default_invoice_date'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
    if request.method == 'POST':
        invoice_data = json.loads(request.body)

        function(invoice_data, org)

    return context


@login_required
@user_passes_test(test, redirect_field_name='/')
def invoice_create(request):
    context = refactor(request, invoice_data_processor, Orders, request.user.tokens.organisation)
    return render(request, 'gstbillingapp/invoice_create.html', context)


@login_required
@user_passes_test(test, redirect_field_name='/')
def purchase_create(request):
    context = refactor(request, product_data_processor, Purchase, request.user.tokens.organisation)
    return render(request, 'gstbillingapp/purchase_create.html', context)


@api_view(["POST"])
def orders(request):
    invoice_data = request.data

    order = invoice_data_processor(invoice_data, request.user.tokens.organisation)

    serializer = OrderSerializer(data=order, many=False)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data, status=200)


@login_required
@user_passes_test(test, redirect_field_name='/')
def invoices(request):
    context = {'orders': Orders.objects.all().order_by('-id')}
    return render(request, 'gstbillingapp/invoices.html', context)


@login_required
@user_passes_test(test, redirect_field_name='/')
def purchases(request):
    context = {'orders': Purchase.objects.filter(organisation=request.user.tokens.organisation).order_by('-id')}
    return render(request, 'gstbillingapp/purchases.html', context)


@login_required
@user_passes_test(test, redirect_field_name='/')
def invoice_delete(request):
    if request.method == "POST":
        invoice_id = request.POST["invoice_id"]
        invoice_obj = get_object_or_404(Orders, organisation=request.user.tokens.organisation, id=invoice_id)
        invoice_obj.delete()
    return redirect('invoices')


@login_required
@user_passes_test(test, redirect_field_name='/')
def customers(request):
    context = {'customers': User.objects.all()}
    return render(request, 'gstbillingapp/customers.html', context)


@login_required
@user_passes_test(test, redirect_field_name='/')
def products(request):
    context = {'products': BillingProduct.objects.filter(organisation=request.user.tokens.organisation)}
    return render(request, 'gstbillingapp/products.html', context)


@login_required
@user_passes_test(test, redirect_field_name='/')
def product_edit(request, product_id):
    product_obj = get_object_or_404(BillingProduct, id=product_id, organisation=request.user.tokens.organisation)

    if request.method == "POST":
        product_form = ProductForm(request.POST, instance=product_obj)
        if product_form.is_valid():
            product_form.save()
            return redirect('products')
    context = {'product_form': ProductForm(instance=product_obj)}
    return render(request, 'gstbillingapp/product_edit.html', context)


@login_required
@user_passes_test(test, redirect_field_name='/')
def invoice_viewer(request, invoice_id):
    invoice_obj = get_object_or_404(Orders, id=invoice_id, organisation=request.user.tokens.organisation)

    return Response(invoice_obj)


@login_required
@user_passes_test(test, redirect_field_name='/')
def show_invoice(request, invoice_id):
    invoice = get_object_or_404(Orders, id=invoice_id, organisation=request.user.tokens.organisation)
    items = OrderItem.objects.filter(order=invoice, organisation=request.user.tokens.organisation)

    context = {"invoice": invoice, "items": items}
    return render(request, 'gstbillingapp/invoice_show.html', context=context)


@login_required
@user_passes_test(test, redirect_field_name='/')
def product_add(request):
    if request.method == "POST":
        product_form = ProductForm(request.POST)

        if product_form.is_valid():
            new_product = product_form.save(commit=False)
            new_product.organisation = request.user.tokens.organisation
            if new_product.product_hsn:
                new_product.product_hsn.gst_percent = new_product.gst_percent
                new_product.product_hsn.gst_percent.save()
            new_product.save()

        print(product_form.errors, product_form.is_valid())

    context = {'product_form': ProductForm()}
    return render(request, 'gstbillingapp/product_edit.html', context)


@login_required
@user_passes_test(test, redirect_field_name='/')
def product_delete(request):
    if request.method == "POST":
        product_id = request.POST["product_id"]
        product_obj = get_object_or_404(BillingProduct, organisation=request.user.tokens.organisation, id=product_id)
        product_obj.delete()
    return redirect('products')


@login_required
@user_passes_test(test, redirect_field_name='/')
def landing_page(request):
    if request.user.tokens.organisation:
        context = {"org": request.user.tokens.organisation}
        return render(request, 'gstbillingapp/pages/landing_page.html', context)
    return redirect('/')


class HSNViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'options']
    queryset = HsnCode.objects.all()
    serializer_class = HSNSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'description', ]


class BillingViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'options']
    queryset = BillingProduct.objects.all()
    serializer_class = BillingProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'product_hsn', 'code', '']

    def get_queryset(self):
        if self.request.user.tokens.organisation:
            return BillingProduct.objects.filter(organisation=self.request.user.tokens.organisation)
        return BillingProduct.objects.none()

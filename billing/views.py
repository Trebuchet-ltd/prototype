import datetime

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from home.models import Orders, OrderItem
from home.models import Product
from .forms import ProductForm
from .utils import invoice_data_processor
from .utils import invoice_data_validator


# Create your views here.


# User Management =====================================


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


@login_required
def invoice_create(request):
    context = {}
    last_order = Orders.objects.all().order_by('-id').first()
    if last_order:
        context['default_invoice_number'] = last_order.id + 1
    else:
        context['default_invoice_number'] = 1

    context['default_invoice_date'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
    if request.method == 'POST':
        invoice_data = request.POST
        validation_error = invoice_data_validator(invoice_data)
        if validation_error:
            context["error_message"] = validation_error
            return render(request, 'gstbillingapp/invoice_create.html', context)
        print("Valid Invoice Data")
        invoice_data_processed = invoice_data_processor(invoice_data)

        customer = None

    return render(request, 'gstbillingapp/invoice_create.html', context)


@login_required
def invoices(request):
    context = {}
    context['orders'] = Orders.objects.all().order_by('-id')
    return render(request, 'gstbillingapp/invoices.html', context)


@login_required
def invoice_viewer(request, invoice_id):
    order = get_object_or_404(Orders, id=invoice_id)
    context = {}
    if order:
        context['items'] = OrderItem.objects.filter(order=order)
    context['order'] = order

    context['currency'] = "₹"
    return render(request, 'gstbillingapp/invoice_printer.html', context)


@login_required
def invoice_delete(request):
    if request.method == "POST":
        invoice_id = request.POST["invoice_id"]
        invoice_obj = get_object_or_404(Orders, user=request.user, id=invoice_id)
        invoice_obj.delete()
    return redirect('invoices')


@login_required
def customers(request):
    context = {}
    context['customers'] = User.objects.all()
    return render(request, 'gstbillingapp/customers.html', context)


@login_required
def products(request):
    context = {}
    context['products'] = Product.objects.all()
    return render(request, 'gstbillingapp/products.html', context)


@login_required
def product_edit(request, product_id):
    product_obj = Product.objects.get(id=product_id)
    if request.method == "POST":
        product_form = ProductForm(request.POST, instance=product_obj)
        if product_form.is_valid():
            new_product = product_form.save()
            return redirect('products')
    context = {}
    context['product_form'] = ProductForm(instance=product_obj)
    return render(request, 'gstbillingapp/product_edit.html', context)


@login_required
def product_add(request):
    if request.method == "POST":
        product_form = ProductForm(request.POST)
        if product_form.is_valid():
            new_product = product_form.save(commit=False)
            new_product.user = request.user
            new_product.save()

            return redirect('products')
    context = {}
    context['product_form'] = ProductForm()
    return render(request, 'gstbillingapp/product_edit.html', context)


@login_required
def product_delete(request):
    if request.method == "POST":
        product_id = request.POST["product_id"]
        product_obj = get_object_or_404(Product, user=request.user, id=product_id)
        product_obj.delete()
    return redirect('products')


def landing_page(request):
    context = {}
    return render(request, 'gstbillingapp/pages/landing_page.html', context)

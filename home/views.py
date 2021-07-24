import json
import random
import string
import razorpay
import requests
from requests.auth import HTTPBasicAuth
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from .models import *
from django.http import HttpResponse
from rest_framework.generics import ListAPIView
from .serializers import *

from django.contrib.auth.decorators import login_required


# Create your views here.
def index(request):
    products = Product.objects.all()
    mainPage = MainPage.objects.all()

    context = {"products": products, "mainpage": mainPage}
    return render(request, template_name="index.html", context=context)


def display_product(request, primary_key):
    inventory = Product.objects.get(id=primary_key)
    if request.method == "POST":
        if (request.user.id is None):
            return HttpResponseRedirect('/login')
        else:
            user = User.objects.get(id=request.user.id)
            cart = user.cart

            inventory_item = cart.items.all().filter(item=inventory)
            print(inventory_item)
            quant_variable = int(request.POST["quantity"])
            if inventory_item:
                inventory_item[0].quantity += quant_variable
                inventory_item[0].save()
                inventory_item = inventory_item[0]
            else:
                inventory_item = CartItem(item=inventory, quantity=quant_variable, cart=cart)
                inventory_item.save()
            cart.total += quant_variable * inventory.price
            cart.save()

        CartItem.quantity = request.POST["quantity"]
        return HttpResponse(json.dumps({'qty': inventory_item.quantity}))
    context = {"products": inventory, 'title': inventory.title}
    return render(request, template_name="display_product.html", context=context)


def link(request):
    return render(request, template_name="link.html")


@login_required
def log_out(request):
    logout(request)
    return HttpResponseRedirect('/')


@login_required
def cart(request):
    context = {}
    user = User.objects.get(id=request.user.id)
    cart = user.cart
    items = cart.items.all()
    for i in items:
        i.range = range(1, i.item.stock + 1)
    print(context)
    context['items'] = items
    context['len_items'] = len(items)
    context['total'] = cart.total
    return render(request, template_name="cart.html", context=context)


@login_required
def delete(request, item_key):
    if request.method == "POST":
        try:
            user = User.objects.get(id=request.user.id)
            item_object = CartItem.objects.get(id=item_key, cart=user.cart)
            total = item_object.item.price * item_object.quantity
            cart_object = item_object.cart
            cart_object.total -= total
            cart_object.save()
            item_object.delete()
            return HttpResponse(json.dumps({'total': cart_object.total, 'items': cart_object.items.count()}))
        except Exception as e:
            print(e)

    return HttpResponseRedirect("/cart")


@login_required
def update(request, update_key):
    if request.method == "POST":
        context = {
        }
        new_cart_quantity = int(request.POST["cart_quantity"])
        try:
            user = User.objects.get(id=request.user.id)
            object_var_from_cart_item = CartItem.objects.get(id=update_key)
            quantity_from_cart_item = object_var_from_cart_item.quantity
            difference_btwn_quantites = new_cart_quantity - quantity_from_cart_item
            object_var_from_cart_item.quantity = new_cart_quantity
            object_var_from_cart_item.save()

            var_of_cart_in_cart_item = object_var_from_cart_item.cart
            current_cart_quantity = object_var_from_cart_item.quantity
            price_from_product_model = object_var_from_cart_item.item.price
            total_price = price_from_product_model * difference_btwn_quantites
            var_of_cart_in_cart_item.total += total_price
            var_of_cart_in_cart_item.save()
            context["total"] = var_of_cart_in_cart_item.total
            updated_cart_item_price = object_var_from_cart_item.quantity * object_var_from_cart_item.item.price

            context[f"price_{update_key}"] = updated_cart_item_price
            context[f"key"] = f"price_{update_key}"

            return HttpResponse(json.dumps(context))
        except Exception as e:
            print(e)

    return HttpResponseRedirect("/cart")


@login_required
def checkout(request):
    context = {}
    user = User.objects.get(id=request.user.id)
    user_addresses = user.Addresses.all()
    context["user_address"] = user_addresses
    items = user.cart.items.all()
    context["len_items"] = len(items)
    context["total"] = user.cart.total
    return render(request, template_name="checkout.html", context=context)


class getProduct(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = getProductSerializer
    http_method_names = ["get"]


@login_required
def addUserDetails(request):
    if request.method == "POST":
        name = request.POST["name"]
        address = request.POST["address"]
        pincode = request.POST["pincode"]
        state = request.POST["state"]
        phone = request.POST["phone"]
        new_address = Addresses(name=name, address=address, pincode=pincode, state=state, phone=phone,
                                user=request.user)

        new_address.save()
    return HttpResponseRedirect("/checkout/")


@login_required
def delivery_options(request):
    context = {}
    user = User.objects.get(id=request.user.id)
    if (request.method == "POST"):
        adid = request.POST["adid"]
    else:
        adid = request.GET["adid"]
        context['errors'] = 'All Fields are Mandatory'
    address = user.Addresses.get(id=adid)
    context["selected_address"] = address

    return render(request, template_name="delivery_options.html", context=context)


def searchResultview(request):
    if (request.method == "GET"):
        query = request.GET["query"]
        model = Product
        template_name = "search_results.html"
        context = {}
        context["search_result"] = Product.objects.filter(meat__icontains=query) | Product.objects.filter(
            title__icontains=query) | Product.objects.filter(description__icontains=query)
        return render(request, template_name, context=context)


@login_required
def confirmOrder(request):
    global paymenturl
    if (request.method == "POST"):
        date = request.POST["date"]
        time = request.POST["time"]
        address = request.POST["selected_address"]
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
            user = User.objects.get(id=request.user.id)
            cart = user.cart
            order = Orders.objects.create(user=request.user, date=date, time=time, address_id=int(address),
                                          total=cart.total)
            order.save()
            amount = 0

            for item in cart.items.all():
                if item.quantity > 0:
                    amount += item.quantity * item.item.price
                elif item.quantity < 0:
                    amount += -item.quantity * item.item.price

                order_item = OrderItem.objects.create(item=item.item, quantity=item.quantity, order=order)
                order_item.save()

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
                        "callback_url": "https://0c9c5151a1b5.ngrok.io/payment",
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
                    return HttpResponseRedirect(paymenturl)
                except Exception as e:
                    print(e)




        except Exception as e:
            print(e)
            return HttpResponseRedirect(f'/delivery_options/?adid={address}')
    return HttpResponseRedirect("/orders/")


def payment(request):
    if request.method == "GET":
        try:
            transactiondetails = TransactionDetails.objects.get(
                transation_id=request.GET["razorpay_payment_link_reference_id"])
            transactiondetails.payment_status = request.GET["razorpay_payment_link_status"]
            transactiondetails.save()
            user = transactiondetails.user
            cart = user.cart
            cart.total = 0
            cart.save()
            for item in cart.items.all():
                item.delete()

        except Exception as ex:
            print(ex)
    return HttpResponseRedirect('https://0c9c5151a1b5.ngrok.io/cart/')


@login_required
def orders(request):
    context = {}
    order = Orders.objects.filter(user=request.user)
    context["orders"] = order
    return render(request, template_name="orders.html", context=context)


@login_required
def order(request, primary_key):
    try:
        order = Orders.objects.get(id=primary_key, user=request.user)
        context = {}
        items = order.order_item.all()
        for i in items:
            i.range = range(1, i.item.stock + 1)
        print(context)
        context['items'] = items
        context['len_items'] = len(items)
        context['total'] = order.total
        return render(request, template_name="order_items.html", context=context)
    except Exception as e:
        print(e)
        return HttpResponseRedirect("/orders/")

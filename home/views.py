import json

from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
# from .models import Product, CartItem, CartModel,MainPage
from .models import *
from django.core import serializers
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
    context = {"products": inventory}
    return render(request, template_name="display_product.html", context=context)


def link(request):
    return render(request, template_name="link.html")


def signin(request):
    context1 = {}
    if request.method == "POST":
        email = request.POST["username"]
        password = request.POST["password"]
        if not email or not password:
            context1['pswderr'] = "Text fields cannot be empty"
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            # Redirect to a success page.
            return HttpResponseRedirect('/')
        else:
            # Return an 'invalid login' error message.
            context1['pswderr'] = "Invalid Credentials"
    context1['sign_text'] = 'Sign In'
    return render((request), template_name="login.html", context=context1)


def signup(request):
    context1 = {}
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        passwrd2 = request.POST["password retype"]
        if not email:
            context1['pswderr'] = 'Email cannot be empty'
        elif not password or not passwrd2:
            context1['pswderr'] = 'Password cannot be empty'
        else:
            if passwrd2 == password:
                try:
                    user = User.objects.create_user(email=email, password=password, username=email)
                    cart = CartModel(user=user, total=0, pincode=0, state='')
                    cart.save()
                    login(request, user)
                    return HttpResponseRedirect('/')

                except Exception as e:
                    print(e)
                    context1['pswderr'] = 'User already exists'
            else:
                context1['pswderr'] = 'Password Does not match'
    context1['sign_text'] = "Register"
    return render(request, template_name="signup.html", context=context1)


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
            item_object = CartItem.objects.get(id=item_key,cart=user.cart)
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
            user = User.objects.get(id = request.user.id)
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
    return HttpResponseRedirect("/")


@login_required
def delivery_options(request):
    if (request.method == "POST"):
        context = {}
        user = User.objects.get(id=request.user.id)
        adid = request.POST["adid"]
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

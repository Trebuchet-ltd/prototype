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
        return HttpResponse(json.dumps({'qty':inventory_item.quantity}))
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
                # try:
                user = User.objects.create_user(email=email, password=password, username=email)
                cart = CartModel(user=user, total=0, address='', pincode=0, state='')
                cart.save()
                login(request, user)
                return HttpResponseRedirect('/')
            # except:
            #     context1['pswderr'] = 'User already exists'
            else:
                context1['pswderr'] = 'Password Does not match'
    context1['sign_text'] = "Register"
    return render(request, template_name="signup.html", context=context1)


def log_out(request):
    logout(request)
    return HttpResponseRedirect('/')


def cart(request):
    context = {}
    user = User.objects.get(id=request.user.id)
    cart = user.cart
    items = cart.items.all()
    context['items'] = items
    return render(request, template_name="cart.html", context=context)


def delete(request, item_key):
    if request.method == "POST":
        item_object = CartItem.objects.get(id=item_key)
        total = item_object.item.price * item_object.quantity
        cart_object = item_object.cart
        cart_object.total -= total
        cart_object.save()
        item_object.delete()

    return HttpResponseRedirect("/cart")


def update(request, update_key):
    if request.method == "POST":
        new_cart_quantity = int(request.POST["cart_quantity"])
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

    return HttpResponseRedirect("/cart")


class getProduct(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = getProductSerializer
    http_method_names = ["get"]

from rest_framework import serializers
from .models import ImageModel, CartModel
from .models import Product
from .models import Tokens, CartItem,TransactionDetails,Orders,OrderItem,Addresses


# from .models import TransactionDetails

class getImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = [
            'title', 'mainimage'
        ]


class getProductSerializer(serializers.ModelSerializer):
    images = getImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'stock', 'meat', 'images', 'bestSeller'
        ]


class GetTokensSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tokens
        fields = [
            'user', 'private_token', 'invite_token', 'invited', 'points', 'reviews',
        ]


class CartItemSerializer(serializers.ModelSerializer):
    item = getProductSerializer(read_only=True,required=False,many=False)
    class Meta:
        model = CartItem
        fields = [
            'item', 'quantity','cart'
        ]
        extra_kwargs = {
            'cart': {'read_only': True},
        }


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = CartModel
        fields = [
            'id','total', "items"
        ]


class TransactionDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDetails
        fields =[
            'transaction_id', 'payment_status'
        ]


class GetAddressSerializer(serializers.ModelSerializer):
    class Meta:
        ordering = ['id']
        model = Addresses
        fields=[
            'id','name','address','pincode','state','phone','latitude','longitude'
            ]


class OrderItemSerializer(serializers.ModelSerializer):
    item = getProductSerializer(read_only=True,required=False,many=False)
    class Meta:
        model = OrderItem
        fields = [
            'item', 'quantity',
        ]

class OrderSerializer(serializers.ModelSerializer):
    order_item = OrderItemSerializer(many=True, read_only=True, required=False)
    address = GetAddressSerializer(read_only=True, required=False)
    transaction = TransactionDetailsSerializer(many=True)
    class Meta:
        model = Orders
        fields = [
            'user','total', 'date', 'time','address','status','order_item','transaction'
        ]

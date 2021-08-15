from rest_framework import serializers
from .models import ImageModel, CartModel
from .models import Product
from .models import Tokens, CartItem, TransactionDetails, Orders, OrderItem, Addresses


class GetImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ImageModel
        fields = [
            'title', 'mainimage','cleaned_image'
        ]


class GetProductSerializer(serializers.ModelSerializer):
    images = GetImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'short_description', 'price', 'stock',
            'meat', 'images', 'bestSeller', "weight", 'rating',
            'weight_variants', 'pieces', 'serves', 'can_be_cleaned', 'cleaned_price',
        ]


class GetTokensSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tokens
        fields = [
            'user', 'private_token', 'invite_token', 'invited', 'points', 'reviews', 'total_points_yet'
        ]


class CartItemSerializer(serializers.ModelSerializer):
    item = GetProductSerializer(read_only=True, required=False, many=False)

    class Meta:
        model = CartItem
        fields = [
            'id', 'item', 'quantity', 'cart', 'weight_variants', 'is_cleaned'
        ]
        extra_kwargs = {
            'cart': {'read_only': True},
        }


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = CartModel
        fields = [
            'id', 'total', "items"
        ]


class TransactionDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDetails
        fields = [
            "id", "payment_status", 'time', 'payment_id'
        ]


class GetAddressSerializer(serializers.ModelSerializer):
    class Meta:
        ordering = ['id']
        model = Addresses
        fields = [
            'id', 'name', 'address', 'pincode', 'state', 'phone', 'latitude', 'longitude', "delivery_charge"
            ]


class OrderItemSerializer(serializers.ModelSerializer):
    item = GetProductSerializer(read_only=True, required=False, many=False)

    class Meta:
        model = OrderItem
        fields = [
            'item', 'quantity', 'weight_variants', 'is_cleaned'
        ]


class OrderSerializer(serializers.ModelSerializer):
    order_item = OrderItemSerializer(many=True, read_only=True, required=False)
    address = GetAddressSerializer(read_only=True, required=False)
    transaction = TransactionDetailsSerializer(read_only=True, many=False, required=False)

    class Meta:
        model = Orders
        fields = [
            'id', 'user', 'total', 'date', 'time', 'address', 'status', 'order_item', 'transaction'
        ]

from rest_framework import serializers
from .models import ImageModel
from .models import Product
from .models import Tokens, CartItem
# from .models import TransactionDetails

class getImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = [
            'title', 'mainimage'
        ]


class getProductSerializer(serializers.ModelSerializer):

    images = getImageSerializer(many=True, required = False)

    class Meta:
        model = Product
        fields = [
            'id','title', 'description', 'price', 'stock', 'meat','images', 'bestSeller'
        ]


class GetTokensSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tokens
        fields = [
            'user', 'private_token', 'invite_token', 'invited', 'points', 'reviews',
        ]


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = [
            'item', 'quantity',"cart"
        ]
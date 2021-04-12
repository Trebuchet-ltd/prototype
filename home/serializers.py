from rest_framework import serializers
from .models import ImageModel
from .models import Product

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
            'id','title', 'description', 'price', 'stock', 'meat','images'
        ]
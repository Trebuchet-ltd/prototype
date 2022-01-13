from django.contrib.auth.models import User, Group
from home.serializers import GetTokensSerializer, CartSerializer, GetAddressSerializer
from rest_framework import serializers


# first we define the serializers
class UserSerializer(serializers.ModelSerializer):
    tokens = GetTokensSerializer(many=False, read_only=True, required=False)
    cart = CartSerializer(many=False, read_only=True, required=False)
    Addresses = GetAddressSerializer(read_only=True, required=False, many=True)

    class Meta:
        model = User
        fields = ('username', 'email', "first_name", "last_name", 'tokens', 'cart', 'id', 'Addresses')


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("name",)

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from home.serializers import *
from .models import *
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt

class ProductViewSet(viewsets.ModelViewSet):
    """

    """
    queryset = Product.objects.all()
    serializer_class = getProductSerializer
    permission_classes = [permissions.IsAuthenticated]

class CartItemViewSets(viewsets.ModelViewSet):
    """
    Api end point to get vart items
    """
    queryset = CartItem.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action

from home.serializers import *
from .models import *
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt


class ProductViewSet(viewsets.ModelViewSet):
    """
    API end point to get all product details
    """
    queryset = Product.objects.all()
    serializer_class = getProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['bestSeller', 'meat']

    # @action(methods=['get'], detail=False, permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    # def front_page(self, request):
    #     best_sellers = Product.objects.all().filter(bestSeller=True)
    #     fish = Product.objects.all().filter(meat='f')
    #     meat = Product.objects.all().filter(meat='m')
    #
    #     page = self.paginate_queryset()
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(best_sellers, many=True)


class CartItemViewSets(viewsets.ModelViewSet):
    """
    Api end point to get cart items
    """
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

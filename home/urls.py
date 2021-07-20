from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views
from .apiviewsets import *


router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'cart_items', CartItemViewSets)


urlpatterns = [
    path(r'', include(router.urls))
]

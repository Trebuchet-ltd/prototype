from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .apiviewsets import *


router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'cart_items', CartItemViewSets)
router.register(r'cart', CartViewSets)
router.register(r'order', OrderViewSets)



urlpatterns = [
    path(r'', include(router.urls)),
    path(r'transaction/', confirm_order),

]

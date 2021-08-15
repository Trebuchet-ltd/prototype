from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apiviewsets import *


router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'cart_items', CartItemViewSets)
router.register(r'cart', CartViewSets)
router.register(r'order', OrderViewSets)
router.register(r'address', AddressViewSets)

urlpatterns = [
    path(r'', include(router.urls)),
    path(r'transaction/', confirm_order),
    path(r'payment/', payment),
    path(r'is_available_pincode/', available_pin_codes),
    path(r'get_coupon/', get_coupon),
    path(r'get_points/', check_points),
    ]

from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register('hsn', views.HSNViewSet)
router.register('bill_products', views.BillingViewSet)

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('', include(router.urls)),
    path('purchases', views.purchases, name='purchases'),
    path('purchases/new', views.purchase_create, name='purchase_create'),

    path('invoices/new', views.invoice_create, name='invoice_create'),
    path('invoices/delete', views.invoice_delete, name='invoice_delete'),
    path('invoices/invoice_viewer/<int:invoice_id>', views.invoice_viewer, name='invoice_viewer'),

    path('login', views.login_view, name='login_view'),
    path('accounts/', include('django.contrib.auth.urls')),
    path(r'order/', views.orders),
    path('invoices', views.invoices, name='invoices'),

    path('products', views.products, name='products'),
    path('products/add', views.product_add, name='product_add'),
    path('products/edit/<int:product_id>', views.product_edit, name='product_edit'),
    path('invoices/<int:invoice_id>', views.show_invoice, name='show_invoice'),
    path('get/<int:invoice_id>', views.get_bill, name='get_bill'),
    path('products/delete', views.product_delete, name='product_delete'),

]

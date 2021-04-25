from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('link/', views.link, name='link'),
    path('login/', views.signin, name='login'),
    path('signup/', views.signup, name='signup'),
    path('product/<int:primary_key>', views.display_product, name='product'),
    path('logout/', views.log_out, name='logout'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('delete/<int:item_key>', views.delete, name='delete'),
    path('update/<int:update_key>', views.update, name='update'),
    path('display/', views.getProduct.as_view(), name='display'),
    path('details/', views.addUserDetails, name='details'),
    path('delivery_options', views.delivery_options, name='delivery_options'),
    path('search/', views.searchResultview, name='search_results')
]

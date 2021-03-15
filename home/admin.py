from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.product)
admin.site.register(models.imageModel)
admin.site.register(models.cartModel)
admin.site.register(models.cart_item)

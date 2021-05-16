from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Product)
admin.site.register(models.ImageModel)
admin.site.register(models.CartModel)
admin.site.register(models.CartItem)
admin.site.register(models.MainPage)
admin.site.register(models.Addresses)

from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Product)
admin.site.register(models.Imagemodel)
admin.site.register(models.CartModel)
admin.site.register(models.Cartitem)
admin.site.register(models.Mainpage)
admin.site.register(models.Addresses)
admin.site.register(models.TransactionDetails)

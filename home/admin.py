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
admin.site.register(models.Orderitem)

@admin.register(models.Orders)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "date","time", "status","address", "orders_products")
    list_filter = ("status", "user", "date",)

    def orders_products(self, obj):

        order_items = models.Orderitem.objects.filter(order=obj)

        try:
            orders = []
            for order_item in order_items:
                orders.append(f" {str(order_item.item).title()} - {order_item.quantity}, ")
            orders[-1] = orders[-1][:-2]

            return "".join(orders)

        except:
            return f"{order_items.item} - {order_items.quantity}"



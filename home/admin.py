from django.contrib import admin,messages
from . import models

# Register your models here.
admin.site.register(models.Product)
admin.site.register(models.ImageModel)
admin.site.register(models.CartModel)
admin.site.register(models.CartItem)
admin.site.register(models.MainPage)
admin.site.register(models.Addresses)
admin.site.register(models.TransactionDetails)

admin.site.register(models.OrderItem)


@admin.register(models.Orders)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "date","time", "status","address", "orders_products","seen_status")
    list_filter = ('is_seen',"status", "user", "date",)

    def orders_products(self, obj):
        order_items = models.OrderItem.objects.filter(order=obj)
        try:
            orders = []
            for order_item in order_items:
                orders.append(f" {str(order_item.item).title()} - {order_item.quantity}, ")
            orders[-1] = orders[-1][:-2]

            return "".join(orders)

        except Exception as e:
            print(e)
            try:
                return f"{order_items.item} - {order_items.quantity}"
            except:
                return "Null"
    def seen_status(self, obj):
        return obj.is_seen == True


    seen_status.boolean = True

    def make_seen(modeladmin, request, queryset):
        queryset.update(is_seen=1)
        messages.success(request, "Selected Record(s) Marked as not seen Successfully !!")

    def make_notseen(modeladmin, request, queryset):
        queryset.update(is_seen=0)
        messages.success(request, "Selected Record(s) Marked as seen Successfully !!")

    admin.site.add_action(make_seen, "Mark as Seen")
    admin.site.add_action(make_notseen, "Mark as not seen")
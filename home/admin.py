from django.contrib import admin,messages
from . import models
import requests

# Register your models here.
admin.site.register(models.Product)
admin.site.register(models.ImageModel)
admin.site.register(models.CartModel)
admin.site.register(models.CartItem)
admin.site.register(models.Addresses)
admin.site.register(models.TransactionDetails)
admin.site.register(models.OrderItem)



@admin.register(models.Orders)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "date","time", "status","address", "orders_products","seen_status")
    list_filter = ('is_seen',"status", "user", "date",)
    actions = ['make_seen','make_not_seen']
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

    def make_not_seen(modeladmin, request, queryset):
        queryset.update(is_seen=0)
        messages.success(request, "Selected Record(s) Marked as seen Successfully !!")



@admin.register(models.AvailableState)
class StatesAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        try:

            url = f'https://cdn-api.co-vin.in/api/v2/admin/location/districts/{obj.state_name}'
            res = requests.get(url,
                               headers=
            {
                'accept': "application/json",
                "Accept-Language": "hi_IN",
                'Host': "cdn-api.co-vin.in",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
            }
                               )

            data = res.json()
            super().save_model(request, obj, form, change)
            state = models.AvailableState.objects.get(state_name=obj.state_name)
            print(state)
            for district in data.get("districts"):
                models.District.objects.create(district_name=district.get("district_name"),state=state)
                pass

        except Exception as ex:
            print(f'Exception {ex}')


@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("district_name","state", "Available_status")
    list_filter =['state','Available_status']
    actions = ['make_available','make_not_Available']
    def available_status(self,obj):
        return obj.Available_status == True
    available_status.boolean = True

    def make_available(modeladmin,request, queryset):
        queryset.update(Available_status=1)
        messages.success(request, "Selected District(s) is available now !!")

    def make_not_Available(modeladmin, request, queryset):
        queryset.update(Available_status=0)
        messages.success(request, "Selected District(s) is not available now !!")


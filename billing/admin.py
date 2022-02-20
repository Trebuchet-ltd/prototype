from django.contrib import admin, messages, messages
from . import models

# Register your models here.
admin.site.register(models.HsnCode)
admin.site.register(models.BillingProduct)


@admin.register(models.BillingProduct)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'available_stock', 'price', 'discount', 'can_be_cleaned','cleaned_price', ]

    search_fields = ['title']

    @admin.display(description="stock")
    def available_stock(self, obj):
        return f"{obj.stock} kg"

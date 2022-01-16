from rest_framework import serializers

from billing.models import HsnCode, BillingProduct


class HSNSerializer(serializers.ModelSerializer):
    class Meta:
        model = HsnCode
        fields = ['code', 'description', 'gst_percent']


class BillingProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingProduct
        fields = ['title', 'product_hsn', 'code', 'price', 'stock', 'discount', 'price2', 'price3', 'gst_percent']

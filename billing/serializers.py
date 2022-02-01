from rest_framework import serializers

from billing.models import HsnCode, BillingProduct


class HSNSerializer(serializers.ModelSerializer):
    class Meta:
        model = HsnCode
        fields = ['code', 'description', 'gst_percent']


class BillingProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingProduct
        fields = ['id', 'title', 'product_hsn', 'code', 'price', 'stock', 'discount', 'price2', 'price3', 'gst_percent']


class SellerSerializer(serializers.ModelSerializer):
    organisation = serializers.ReadOnlyField(source='organisation.name')

    class Meta:
        model = BillingProduct
        fields = ['id', 'organisation', 'stock', 'discount', 'price', 'gst_percent', 'can_be_cleaned', 'cleaned_price']

from rest_framework import serializers

from billing.models import HsnCode


class HSNSerializer(serializers.ModelSerializer):
    class Meta:
        model = HsnCode
        fields = ['code', 'description', 'gst_percent']

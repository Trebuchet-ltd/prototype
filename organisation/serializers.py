from rest_framework import serializers

from home.serializers import GetAddressSerializer
from .models import Organisation


class OrganisationSerializer(serializers.ModelSerializer):
    address = GetAddressSerializer(read_only=True, required=False, many=False)

    class Meta:
        model = Organisation
        fields = [
            'id', 'name', 'address', 'show_on_website'
        ]

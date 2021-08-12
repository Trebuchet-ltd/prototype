from rest_framework import serializers


class TokensSerializer(serializers.Serializer, ):
    grant_type = serializers.CharField(max_length=5000)
    client_id = serializers.CharField(max_length=5000)
    client_secret = serializers.CharField(max_length=5000)
    backend = serializers.CharField(max_length=5000)
    token = serializers.CharField(max_length=5000)

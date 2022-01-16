from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions

from organisation.models import Organisation
from organisation.serializers import OrganisationSerializer


class OrganisationViewSets(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer
    http_method_names = ['get', ]


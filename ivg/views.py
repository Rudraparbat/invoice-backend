from django.shortcuts import render
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
# Create your views here.

class HealthCheckViewSet(APIView):
    def get(self, request):
        return Response({
            "success": True,
            "data": "Server Healthy", 
            "error": None
        })
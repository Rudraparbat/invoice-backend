
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import HealthCheckViewSet, InvoiceCreationViewSet

router = DefaultRouter()
router.register("invoice" , InvoiceCreationViewSet , basename='invoice')

urlpatterns = [
    path("", include("dj_rest_auth.urls")),
    path("", include("dj_rest_auth.registration.urls")),
    path('health/', HealthCheckViewSet.as_view(), name='health'),
    path('' , include(router.urls))
]
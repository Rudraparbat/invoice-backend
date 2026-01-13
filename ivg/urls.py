
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, HealthCheckViewSet, InvoiceCreationViewSet, UserManagementViewSet

router = DefaultRouter()
router.register("invoice" , InvoiceCreationViewSet , basename='invoice')

branch_router = DefaultRouter()
branch_router.register("" , BranchViewSet , basename='branch')

user_manage_router = DefaultRouter()
user_manage_router.register("users" , UserManagementViewSet , basename='user')
urlpatterns = [
    path("", include("dj_rest_auth.urls")),
    path("", include("dj_rest_auth.registration.urls")),
    path('health/', HealthCheckViewSet.as_view(), name='health'),
    path('' , include(router.urls))
]
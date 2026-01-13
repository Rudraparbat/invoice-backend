# permissions.py
from rest_framework import permissions
from .models import InvoiceUser


class UltraAdminPermission(permissions.BasePermission):
    """
    Permission for UltraAdminPermission
    """
    def has_permission(self, request, view):
        return request.user.is_ultraadmin

class SuperAdminPermission(permissions.BasePermission):
    """
    Permission for SuperAdminPermission
    """
    def has_permission(self, request, view):
        return request.user.is_superadmin

class CoOfficerPermission(permissions.BasePermission):
    """
    Permissions for CoOfficerPermission
    """
    def has_permission(self, request, view):
        return request.user.is_co_officer

class AdminPermission(permissions.BasePermission):
    """
    Permissions for AdminPermission
    """
    def has_permission(self, request, view):
        return request.user.is_admin

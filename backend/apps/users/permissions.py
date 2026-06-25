"""Custom permissions for role-based access control."""
from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allow access only to admin role users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsOwnerOrAdmin(BasePermission):
    """Allow access to object owner or admin users."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        # Check if the object has a user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # For user objects themselves
        return obj == request.user

from rest_framework.permissions import BasePermission
from .models import UserProfile


class IsAdminUser(BasePermission):
    """
    Permission class to check if the user has admin role.
    Only users with role = 'admin' can access the resource.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and hasattr(request.user, 'profile')
            and request.user.profile.role == UserProfile.Role.ADMIN
        )

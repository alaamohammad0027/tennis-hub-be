from rest_framework.permissions import BasePermission
from accounts.models.users import UserType


class IsAdmin(BasePermission):
    """Permission for admin operations"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.user_type == UserType.ADMIN

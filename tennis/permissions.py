from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.models.users import UserType


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.user_type == UserType.ADMIN
        )


class IsClubAdmin(BasePermission):
    """User who registered as a club."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "club_profile")
        )


class IsFederationAdmin(BasePermission):
    """User who registered as a federation."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "federation_profile")
        )


class IsCoach(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "coach_profile")
        )


class IsAdminOrCoach(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == UserType.ADMIN or hasattr(
            request.user, "coach_profile"
        )


class IsAdminOrClub(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == UserType.ADMIN or hasattr(
            request.user, "club_profile"
        )


class IsAdminOrClubOrFederation(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.user_type == UserType.ADMIN
            or hasattr(request.user, "club_profile")
            or hasattr(request.user, "federation_profile")
        )

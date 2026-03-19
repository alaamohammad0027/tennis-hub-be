from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions.base import IsAdmin
from accounts.models import User
from accounts.serializers import (
    UserBaseSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter


class UserViewSet(viewsets.ModelViewSet):
    """
    Admin-only CRUD for users.
    - List, create, retrieve, update, deactivate users
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    swagger_tags = ["Users"]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["user_type", "is_active"]
    search_fields = ["email", "first_name", "last_name", "phone_number"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()
        return User.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserBaseSerializer

    def destroy(self, request, *args, **kwargs):
        """Soft-delete: deactivate user instead of deleting"""
        user = self.get_object()
        if user == request.user:
            return Response(
                {"error": "You cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)

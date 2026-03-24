from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from accounts.models.choices import UserType
from core.permissions.base import IsAdmin


class _ProfileBase(ReadOnlyModelViewSet):
    """
    Shared base for all profile viewsets.

    Access rules:
      Admin      → sees all profiles of any type, can approve/reject any
      Federation → sees own profile + linked clubs; can approve/reject linked clubs
      Club       → sees own profile + affiliated coaches/players/referees; can approve/reject them
      Others     → see only their own profile, no verification actions
    """

    http_method_names = ["get", "post", "head", "options"]
    filter_backends = [DjangoFilterBackend, SearchFilter]

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_serializer(self, *args, **kwargs):
        """Admin → all fields. Everyone else → PUBLIC_FIELDS."""
        if "fields" not in kwargs:
            serializer_class = self.get_serializer_class()
            if self.request.user.user_type != UserType.ADMIN and hasattr(
                serializer_class, "PUBLIC_FIELDS"
            ):
                kwargs["fields"] = serializer_class.PUBLIC_FIELDS
        return super().get_serializer(*args, **kwargs)

    def _can_verify(self, request, profile):
        """Override per viewset to define who may approve/reject this profile type."""
        return request.user.user_type == UserType.ADMIN

    def _do_approve(self, request, pk):
        from accounts.models.profiles.base import VerificationStatus

        profile = self.get_object()
        if not self._can_verify(request, profile):
            return Response(
                {"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN
            )
        if profile.verification_status == VerificationStatus.APPROVED:
            return Response(
                {"detail": "Profile is already approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile.approve(by_user=request.user)
        return Response(self.get_serializer(profile).data)

    def _do_reject(self, request, pk):
        profile = self.get_object()
        if not self._can_verify(request, profile):
            return Response(
                {"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN
            )
        reason = request.data.get("reason", "")
        if not reason:
            return Response(
                {"detail": "A rejection reason is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile.reject(by_user=request.user, reason=reason)
        return Response(self.get_serializer(profile).data)

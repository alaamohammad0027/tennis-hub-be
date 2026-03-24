from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.filters import UserFilter
from accounts.models import User, UserType
from accounts.serializers import (
    UserBaseSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)
from core.permissions.base import IsAdmin


def _related_user_ids(user):
    """
    Returns a queryset of User IDs visible to non-admin users based on their type:
      Club       → affiliated coaches, players, referees
      Federation → linked club users
      Others     → just themselves
    """
    if user.user_type == "club":
        from tennis.models import Affiliation, AffiliationLinkType

        affiliated_user_ids = Affiliation.objects.filter(
            target=user,
            link_type__in=[
                AffiliationLinkType.COACH_CLUB,
                AffiliationLinkType.PLAYER_CLUB,
                AffiliationLinkType.REFEREE_CLUB,
            ],
        ).values_list("requester_id", flat=True)
        return list(affiliated_user_ids)

    if user.user_type == "federation":
        from tennis.models import Affiliation, AffiliationLinkType

        return list(
            Affiliation.objects.filter(
                target=user,
                link_type=AffiliationLinkType.CLUB_FEDERATION,
            ).values_list("requester_id", flat=True)
        )

    return [user.pk]


@extend_schema_view(
    list=extend_schema(
        tags=["Management"],
        summary="List users",
        description=(
            "Returns users visible to the authenticated user based on their role:\n\n"
            "| Role | Visible users |\n"
            "|---|---|\n"
            "| **Admin** | All users in the platform |\n"
            "| **Club** | Affiliated coaches, players, and referees |\n"
            "| **Federation** | Club users linked to their federation |\n"
            "| **Others** | Only themselves |\n\n"
            "Write actions (create / update / delete) are **Admin only**."
        ),
    ),
    retrieve=extend_schema(
        tags=["Management"],
        summary="Get user detail",
        description="Returns a single user. Access is limited to users visible to you (same rules as list).",
    ),
    create=extend_schema(
        tags=["Management"],
        summary="Create user (Admin only)",
        description="**Admin only.** Creates a new user account directly (bypasses registration/OTP flow).",
    ),
    update=extend_schema(
        tags=["Management"],
        summary="Update user (Admin only)",
        description="**Admin only.** Full update of a user account.",
    ),
    partial_update=extend_schema(
        tags=["Management"],
        summary="Partially update user (Admin only)",
        description="**Admin only.** Partial update of a user account.",
    ),
    destroy=extend_schema(
        tags=["Management"],
        summary="Deactivate user (Admin only)",
        description="**Admin only.** Soft-deletes the account by setting `is_active=False`. The account is not permanently deleted.",
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = UserFilter
    search_fields = ["email", "first_name", "last_name", "phone_number"]

    def get_permissions(self):
        # Write actions: admin only
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdmin()]
        # Read actions: any authenticated user (queryset scoped by type)
        return [IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()

        user = self.request.user

        if user.user_type == UserType.ADMIN:
            return User.objects.order_by("-created_at")

        ids = _related_user_ids(user)
        return User.objects.filter(pk__in=ids).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserBaseSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "You cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)

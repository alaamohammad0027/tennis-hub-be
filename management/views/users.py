from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from rest_framework import serializers, status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import (
    User,
    UserProfileType,
    FederationProfile,
    ClubProfile,
    CoachProfile,
    RefereeProfile,
    PlayerProfile,
    FanProfile,
)
from accounts.models.choices import UserType
from accounts.models.profiles.base import VerificationStatus
from core.permissions.base import IsAdmin
from core.services.serializers import DynamicFieldsModelSerializer


class UserManagementSerializer(DynamicFieldsModelSerializer):
    """Lightweight user list for admin — email, phone, name, type."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "user_type",
            "is_active",
            "email_verified",
            "date_joined",
        ]
        read_only_fields = fields


@extend_schema_view(
    list=extend_schema(
        tags=["Management"],
        summary="List all users (Admin)",
        description="Admin-only full user list. Supports filtering by `user_type`, `is_active`, `email_verified` and search by name/email/phone.",
    ),
    retrieve=extend_schema(
        tags=["Management"],
        summary="Get user detail (Admin)",
        description="Admin-only. Retrieve a single user's full details.",
    ),
)
class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin-only: list and retrieve all users."""

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = UserManagementSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["user_type", "is_active", "email_verified"]
    search_fields = ["email", "first_name", "last_name", "phone_number"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()
        return User.objects.order_by("-date_joined")


# ─────────────────────────────────────────────────────────────
# Change role — deactivate / reactivate profiles, never delete
# ─────────────────────────────────────────────────────────────

# Maps user_type → OneToOne reverse accessor on User
_PROFILE_ATTR_MAP = {
    UserProfileType.FEDERATION: "federation_profile",
    UserProfileType.CLUB: "club_profile",
    UserProfileType.COACH: "coach_profile",
    UserProfileType.REFEREE: "referee_profile",
    UserProfileType.PLAYER: "player_profile",
    UserProfileType.FAN: "fan_profile",
}


def _deactivate_current_profile(user):
    """Set the user's active profile to is_active=False (not deleted — restorable)."""
    for attr in _PROFILE_ATTR_MAP.values():
        profile = getattr(user, attr, None)
        if profile is not None and profile.is_active:
            profile.is_active = False
            profile.save(update_fields=["is_active"])
            return


def _activate_or_create_profile(user, new_type, data):
    """
    If the user previously had a profile of new_type (now inactive), restore it.
    Otherwise create a fresh profile.
    Returns (profile, restored: bool).
    """
    attr = _PROFILE_ATTR_MAP.get(new_type)
    existing = getattr(user, attr, None) if attr else None

    if existing is not None:
        # Previous profile found — just reactivate it (all data is preserved)
        existing.is_active = True
        existing.save(update_fields=["is_active"])
        return existing, True

    # No previous profile for this type — create a new one
    profile = _create_fresh_profile(user, new_type, data)
    return profile, False


def _create_fresh_profile(user, new_type, data):
    if new_type == UserProfileType.FEDERATION:
        if not data.get("federation_name"):
            raise serializers.ValidationError(
                {"federation_name": "Required when changing to federation."}
            )
        return FederationProfile.objects.create(
            user=user,
            federation_name=data["federation_name"],
            country=data.get("country", ""),
            contact_email=user.email,
            contact_phone=user.phone_number,
            verification_status=VerificationStatus.PENDING,
        )
    if new_type == UserProfileType.CLUB:
        if not data.get("club_name"):
            raise serializers.ValidationError(
                {"club_name": "Required when changing to club."}
            )
        return ClubProfile.objects.create(
            user=user,
            club_name=data["club_name"],
            club_type=data.get("club_type", "club"),
            country=data.get("country", ""),
            contact_email=user.email,
            contact_phone=user.phone_number,
            verification_status=VerificationStatus.PENDING,
        )
    if new_type == UserProfileType.COACH:
        return CoachProfile.objects.create(
            user=user,
            specialization=data.get("specialization", ""),
            coaching_level=data.get("coaching_level", "intermediate"),
            verification_status=VerificationStatus.PENDING,
        )
    if new_type == UserProfileType.REFEREE:
        return RefereeProfile.objects.create(
            user=user,
            referee_level=data.get("referee_level", "local"),
            verification_status=VerificationStatus.PENDING,
        )
    if new_type == UserProfileType.PLAYER:
        return PlayerProfile.objects.create(
            user=user,
            skill_level=data.get("skill_level", "beginner"),
            dominant_hand=data.get("dominant_hand", "right"),
            nationality=data.get("nationality", ""),
            verification_status=VerificationStatus.PENDING,
        )
    if new_type == UserProfileType.FAN:
        return FanProfile.objects.create(
            user=user,
            nationality=data.get("nationality", ""),
            verification_status=VerificationStatus.PENDING,
        )
    # UserType.ADMIN — no profile model needed
    return None


class _ChangeRoleSerializer(serializers.Serializer):
    new_type = serializers.ChoiceField(choices=UserType.choices)
    # Only needed when switching TO federation/club for the first time (no previous profile)
    federation_name = serializers.CharField(required=False, allow_blank=True)
    club_name = serializers.CharField(required=False, allow_blank=True)
    club_type = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    specialization = serializers.CharField(required=False, allow_blank=True)
    coaching_level = serializers.CharField(required=False, allow_blank=True)
    referee_level = serializers.CharField(required=False, allow_blank=True)
    skill_level = serializers.CharField(required=False, allow_blank=True)
    dominant_hand = serializers.CharField(required=False, allow_blank=True)
    nationality = serializers.CharField(required=False, allow_blank=True)


class _CreateAdminSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(
        max_length=20, required=False, allow_blank=True, default=""
    )

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()


@extend_schema(
    tags=["Management"],
    request=_CreateAdminSerializer,
    summary="Create an admin account (Admin only)",
    description=(
        "**Admin only.** Create a new platform admin account directly — no OTP, no profile.\n\n"
        "The new account is active and email-verified immediately."
    ),
    examples=[
        OpenApiExample(
            "Request",
            request_only=True,
            value={
                "email": "newadmin@tennispass.com",
                "password": "SecurePass123",
                "first_name": "New",
                "last_name": "Admin",
                "phone_number": "+966500000000",
            },
        ),
    ],
)
class CreateAdminView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = _CreateAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone_number=data.get("phone_number", ""),
            user_type=UserType.ADMIN,
            is_active=True,
            email_verified=True,
        )
        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.get_full_name(),
                "user_type": user.user_type,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Management"],
    request=_ChangeRoleSerializer,
    summary="Change user role (Admin)",
    description=(
        "**Admin only.** Change a user's role.\n\n"
        "**Profile data is never deleted.** If the user previously had a profile of the target type "
        "(e.g. was a coach before), it is **restored** with all its original data intact. "
        "If no previous profile exists for that type, a fresh one is created.\n\n"
        "The current active profile is set to `is_active=False` (deactivated, not deleted).\n\n"
        "**Extra fields are only needed when creating a new profile for the first time:**\n"
        "- `federation` → `federation_name` (+ optional `country`)\n"
        "- `club` → `club_name` (+ optional `club_type`, `country`)\n"
        "- `coach / referee / player / fan` → all optional, use defaults if omitted\n\n"
        "If restoring a previous profile, these fields are ignored — the old data is used as-is."
    ),
    examples=[
        OpenApiExample(
            "Coach → Player (first time as player)",
            value={"new_type": "player", "skill_level": "intermediate"},
            request_only=True,
        ),
        OpenApiExample(
            "Player → Coach (restoring previous coach profile)",
            value={"new_type": "coach"},
            request_only=True,
        ),
        OpenApiExample(
            "Coach → Club (first time as club)",
            value={"new_type": "club", "club_name": "Elite Academy", "country": "SA"},
            request_only=True,
        ),
    ],
)
class ChangeRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        serializer = _ChangeRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        new_type = data["new_type"]

        if user.user_type == new_type:
            return Response(
                {"detail": f"User already has role '{new_type}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            _deactivate_current_profile(user)
            _, restored = _activate_or_create_profile(user, new_type, data)
            user.user_type = new_type
            user.save(update_fields=["user_type"])

        if new_type == UserType.ADMIN:
            detail = f"Role changed to 'admin'. Previous profile deactivated."
        else:
            action = "restored" if restored else "created"
            detail = f"Role changed to '{new_type}'. Previous profile deactivated. {new_type.capitalize()} profile {action}."

        return Response(
            {
                "detail": detail,
                "user_id": str(user.id),
                "new_type": new_type,
                "profile_restored": restored,
            },
            status=status.HTTP_200_OK,
        )

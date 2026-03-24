"""
accounts/serializers/me.py

Per-type serializers for PATCH /me.

All fields are flat — no nested `profile` key.
User fields (first_name, last_name, phone_number, photo) and profile fields
are all at the top level. The update() method splits them automatically.
"""

from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from accounts.models import (
    FederationProfile,
    ClubProfile,
    CoachProfile,
    RefereeProfile,
    PlayerProfile,
    FanProfile,
)
from accounts.models.choices import UserType
from accounts.serializers.profiles import (
    FederationProfileSerializer,
    ClubProfileSerializer,
    CoachProfileSerializer,
    RefereeProfileSerializer,
    PlayerProfileSerializer,
    FanProfileSerializer,
)


# ─────────────────────────────────────────────────────────────
# GET /me profile read map
# Uses the shared profile serializers with ME_FIELDS preset
# (admin fields minus the redundant `user` object).
# ─────────────────────────────────────────────────────────────

ME_PROFILE_READ_MAP = {
    UserType.FEDERATION: (FederationProfile, FederationProfileSerializer),
    UserType.CLUB: (ClubProfile, ClubProfileSerializer),
    UserType.COACH: (CoachProfile, CoachProfileSerializer),
    UserType.REFEREE: (RefereeProfile, RefereeProfileSerializer),
    UserType.PLAYER: (PlayerProfile, PlayerProfileSerializer),
    UserType.FAN: (FanProfile, FanProfileSerializer),
}


# ─────────────────────────────────────────────────────────────
# Base PATCH /me serializer
# User fields are declared here. Profile fields are in subclasses.
# update() splits by _USER_FIELDS — no nested key needed.
# ─────────────────────────────────────────────────────────────

_USER_FIELDS = frozenset(
    [
        "first_name",
        "last_name",
        "phone_number",
        "photo",
        "nationality",
        "date_of_birth",
        "bio",
    ]
)


class _BaseMeUpdateSerializer(serializers.Serializer):
    """
    Base for per-type PATCH /me serializers.
    All fields flat — subclasses add type-specific profile fields directly.
    """

    PROFILE_ATTR = None  # e.g. "coach_profile"

    # ── User fields ──────────────────────────────────────────
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone_number = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    photo = serializers.ImageField(required=False, allow_null=True)
    nationality = CountryField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    def update(self, user, validated_data):
        user_data = {k: v for k, v in validated_data.items() if k in _USER_FIELDS}
        profile_data = {
            k: v for k, v in validated_data.items() if k not in _USER_FIELDS
        }

        if user_data:
            for field, value in user_data.items():
                setattr(user, field, value)
            user.save(update_fields=list(user_data.keys()))

        if profile_data and self.PROFILE_ATTR:
            profile = getattr(user, self.PROFILE_ATTR, None)
            if profile:
                for field, value in profile_data.items():
                    setattr(profile, field, value)
                profile.save(update_fields=list(profile_data.keys()))

        return user


# ─────────────────────────────────────────────────────────────
# Per-type PATCH /me serializers — all fields flat at top level
# ─────────────────────────────────────────────────────────────


class FederationMeUpdateSerializer(_BaseMeUpdateSerializer):
    PROFILE_ATTR = "federation_profile"

    # ── Profile fields ───────────────────────────────────────
    federation_name = serializers.CharField(max_length=200, required=False)
    sport = serializers.CharField(max_length=30, required=False)
    country = CountryField(required=False, allow_blank=True)
    founding_year = serializers.IntegerField(required=False, allow_null=True)
    registration_number = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    logo = serializers.ImageField(required=False, allow_null=True)
    website = serializers.URLField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False)
    contact_phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    description = serializers.CharField(required=False, allow_blank=True)


class ClubMeUpdateSerializer(_BaseMeUpdateSerializer):
    PROFILE_ATTR = "club_profile"

    # ── Profile fields ───────────────────────────────────────
    club_name = serializers.CharField(max_length=200, required=False)
    club_type = serializers.CharField(max_length=30, required=False)
    country = CountryField(required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    founding_year = serializers.IntegerField(required=False, allow_null=True)
    registration_number = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    logo = serializers.ImageField(required=False, allow_null=True)
    website = serializers.URLField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False)
    contact_phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    description = serializers.CharField(required=False, allow_blank=True)
    facility_count = serializers.IntegerField(min_value=0, required=False)


class CoachMeUpdateSerializer(_BaseMeUpdateSerializer):
    PROFILE_ATTR = "coach_profile"

    # ── Profile fields ───────────────────────────────────────
    specialization = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )
    coaching_level = serializers.CharField(max_length=20, required=False)
    license_number = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    certifications = serializers.CharField(required=False, allow_blank=True)
    years_experience = serializers.IntegerField(min_value=0, required=False)


class RefereeMeUpdateSerializer(_BaseMeUpdateSerializer):
    PROFILE_ATTR = "referee_profile"

    # ── Profile fields ───────────────────────────────────────
    referee_level = serializers.CharField(max_length=20, required=False)
    license_number = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    certifications = serializers.CharField(required=False, allow_blank=True)
    years_experience = serializers.IntegerField(min_value=0, required=False)
    itf_badge = serializers.CharField(max_length=100, required=False, allow_blank=True)


class PlayerMeUpdateSerializer(_BaseMeUpdateSerializer):
    PROFILE_ATTR = "player_profile"

    # ── Profile fields ───────────────────────────────────────
    skill_level = serializers.CharField(max_length=20, required=False)
    dominant_hand = serializers.CharField(max_length=20, required=False)


class FanMeUpdateSerializer(_BaseMeUpdateSerializer):
    PROFILE_ATTR = "fan_profile"

    # ── Profile fields ───────────────────────────────────────
    favorite_club = serializers.UUIDField(required=False, allow_null=True)


class AdminMeUpdateSerializer(_BaseMeUpdateSerializer):
    """Admin users have no profile model — only user account fields."""

    PROFILE_ATTR = None


# ─────────────────────────────────────────────────────────────
# Dispatch map
# ─────────────────────────────────────────────────────────────

ME_UPDATE_MAP = {
    UserType.FEDERATION: FederationMeUpdateSerializer,
    UserType.CLUB: ClubMeUpdateSerializer,
    UserType.COACH: CoachMeUpdateSerializer,
    UserType.REFEREE: RefereeMeUpdateSerializer,
    UserType.PLAYER: PlayerMeUpdateSerializer,
    UserType.FAN: FanMeUpdateSerializer,
    UserType.ADMIN: AdminMeUpdateSerializer,
}

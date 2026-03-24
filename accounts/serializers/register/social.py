from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from accounts.models import (
    UserProfileType,
    FederationProfile,
    ClubProfile,
    CoachProfile,
    RefereeProfile,
    PlayerProfile,
    FanProfile,
)
from accounts.models.profiles.base import VerificationStatus


class CompleteProfileSerializer(serializers.Serializer):
    """Used after Google login (is_new_user=True) to pick a type and fill the profile."""

    user_type = serializers.ChoiceField(choices=UserProfileType.choices)

    # Per-type optional fields (frontend sends only relevant ones)
    federation_name = serializers.CharField(required=False, allow_blank=True)
    country = CountryField(required=False, allow_blank=True)
    club_name = serializers.CharField(required=False, allow_blank=True)
    club_type = serializers.CharField(required=False, allow_blank=True)
    specialization = serializers.CharField(required=False, allow_blank=True)
    coaching_level = serializers.CharField(required=False, allow_blank=True)
    referee_level = serializers.CharField(required=False, allow_blank=True)
    skill_level = serializers.CharField(required=False, allow_blank=True)
    dominant_hand = serializers.CharField(required=False, allow_blank=True)
    nationality = CountryField(required=False, allow_blank=True)

    def validate(self, attrs):
        t = attrs["user_type"]
        if t == UserProfileType.FEDERATION and not attrs.get("federation_name"):
            raise serializers.ValidationError(
                {"federation_name": _("Required for federation.")}
            )
        if t == UserProfileType.CLUB and not attrs.get("club_name"):
            raise serializers.ValidationError({"club_name": _("Required for club.")})
        return attrs

    @transaction.atomic
    def save(self, user):
        data = self.validated_data
        t = data["user_type"]
        PROFILE_ATTRS = (
            "federation_profile",
            "club_profile",
            "coach_profile",
            "referee_profile",
            "player_profile",
            "fan_profile",
        )
        if any(hasattr(user, a) for a in PROFILE_ATTRS):
            raise serializers.ValidationError(_("Profile already completed."))

        if t == UserProfileType.FEDERATION:
            FederationProfile.objects.create(
                user=user,
                federation_name=data["federation_name"],
                country=data.get("country", ""),
                contact_email=user.email,
                verification_status=VerificationStatus.PENDING,
            )
        elif t == UserProfileType.CLUB:
            ClubProfile.objects.create(
                user=user,
                club_name=data["club_name"],
                club_type=data.get("club_type", "club"),
                contact_email=user.email,
                verification_status=VerificationStatus.PENDING,
            )
        elif t == UserProfileType.COACH:
            CoachProfile.objects.create(
                user=user,
                specialization=data.get("specialization", ""),
                coaching_level=data.get("coaching_level", "intermediate"),
                verification_status=VerificationStatus.PENDING,
            )
        elif t == UserProfileType.REFEREE:
            RefereeProfile.objects.create(
                user=user,
                referee_level=data.get("referee_level", "local"),
                verification_status=VerificationStatus.PENDING,
            )
        elif t == UserProfileType.PLAYER:
            PlayerProfile.objects.create(
                user=user,
                skill_level=data.get("skill_level", "beginner"),
                dominant_hand=data.get("dominant_hand", "right"),
                nationality=data.get("nationality", ""),
                verification_status=VerificationStatus.PENDING,
            )
        elif t == UserProfileType.FAN:
            FanProfile.objects.create(
                user=user,
                nationality=data.get("nationality", ""),
                verification_status=VerificationStatus.APPROVED,
            )
        return user

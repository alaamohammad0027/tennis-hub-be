from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from accounts.models import ClubProfile, UserProfileType
from accounts.models.profiles.base import VerificationStatus
from accounts.serializers.register.base import BaseRegisterSerializer


class ClubRegisterSerializer(BaseRegisterSerializer):
    USER_TYPE = UserProfileType.CLUB

    # ── Profile fields ───────────────────────────────────────
    club_name = serializers.CharField(max_length=200)
    club_type = serializers.CharField(max_length=30, required=False, default="club")
    country = CountryField(required=False, allow_blank=True, default="")
    city = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    address = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )
    registration_number = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    website = serializers.URLField(required=False, allow_blank=True, default="")

    def _create_profile(self, user, data):
        ClubProfile.objects.create(
            user=user,
            club_name=data["club_name"],
            club_type=data.get("club_type", "club"),
            country=data.get("country", ""),
            city=data.get("city", ""),
            address=data.get("address", ""),
            registration_number=data.get("registration_number", ""),
            website=data.get("website", ""),
            contact_email=user.email,
            contact_phone=user.phone_number,
            verification_status=VerificationStatus.PENDING,
        )

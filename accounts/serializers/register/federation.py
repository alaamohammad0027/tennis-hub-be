from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from accounts.models import FederationProfile, UserProfileType
from accounts.models.profiles.base import VerificationStatus
from accounts.serializers.register.base import BaseRegisterSerializer


class FederationRegisterSerializer(BaseRegisterSerializer):
    USER_TYPE = UserProfileType.FEDERATION

    # ── Profile fields ───────────────────────────────────────
    federation_name = serializers.CharField(max_length=200)
    sport = serializers.CharField(max_length=30, required=False, default="tennis")
    country = CountryField()
    founding_year = serializers.IntegerField(required=False, allow_null=True)
    registration_number = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    website = serializers.URLField(required=False, allow_blank=True, default="")

    def _create_profile(self, user, data):
        FederationProfile.objects.create(
            user=user,
            federation_name=data["federation_name"],
            sport=data.get("sport", "tennis"),
            country=data["country"],
            founding_year=data.get("founding_year"),
            registration_number=data.get("registration_number", ""),
            website=data.get("website", ""),
            contact_email=user.email,
            contact_phone=user.phone_number,
            verification_status=VerificationStatus.PENDING,
        )

from rest_framework import serializers

from accounts.models import RefereeProfile, UserProfileType
from accounts.models.profiles.base import VerificationStatus
from accounts.serializers.register.base import BaseRegisterSerializer


class RefereeRegisterSerializer(BaseRegisterSerializer):
    USER_TYPE = UserProfileType.REFEREE

    # ── Profile fields ───────────────────────────────────────
    referee_level = serializers.CharField(
        max_length=20, required=False, default="local"
    )
    license_number = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    years_experience = serializers.IntegerField(min_value=0, default=0)
    itf_badge = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )

    def _create_profile(self, user, data):
        RefereeProfile.objects.create(
            user=user,
            referee_level=data.get("referee_level", "local"),
            license_number=data.get("license_number", ""),
            years_experience=data.get("years_experience", 0),
            itf_badge=data.get("itf_badge", ""),
            verification_status=VerificationStatus.PENDING,
        )

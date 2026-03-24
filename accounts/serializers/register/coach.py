from rest_framework import serializers

from accounts.models import CoachProfile, UserProfileType
from accounts.models.profiles.base import VerificationStatus
from accounts.serializers.register.base import BaseRegisterSerializer


class CoachRegisterSerializer(BaseRegisterSerializer):
    USER_TYPE = UserProfileType.COACH

    # ── Profile fields ───────────────────────────────────────
    specialization = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    coaching_level = serializers.CharField(
        max_length=20, required=False, default="intermediate"
    )
    license_number = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    years_experience = serializers.IntegerField(min_value=0, default=0)

    def _create_profile(self, user, data):
        CoachProfile.objects.create(
            user=user,
            specialization=data.get("specialization", ""),
            coaching_level=data.get("coaching_level", "intermediate"),
            license_number=data.get("license_number", ""),
            years_experience=data.get("years_experience", 0),
            verification_status=VerificationStatus.PENDING,
        )

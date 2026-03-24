from rest_framework import serializers

from accounts.models import PlayerProfile, UserProfileType
from accounts.models.profiles.base import VerificationStatus
from accounts.serializers.register.base import BaseRegisterSerializer


class PlayerRegisterSerializer(BaseRegisterSerializer):
    USER_TYPE = UserProfileType.PLAYER

    # ── Profile fields ───────────────────────────────────────
    skill_level = serializers.CharField(
        max_length=20, required=False, default="beginner"
    )
    dominant_hand = serializers.CharField(
        max_length=20, required=False, default="right"
    )

    def _create_profile(self, user, data):
        PlayerProfile.objects.create(
            user=user,
            skill_level=data.get("skill_level", "beginner"),
            dominant_hand=data.get("dominant_hand", "right"),
            verification_status=VerificationStatus.PENDING,
        )

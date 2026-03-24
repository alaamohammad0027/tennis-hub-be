from accounts.models import FanProfile, UserProfileType
from accounts.models.profiles.base import VerificationStatus
from accounts.serializers.register.base import BaseRegisterSerializer


class FanRegisterSerializer(BaseRegisterSerializer):
    USER_TYPE = UserProfileType.FAN

    def _create_profile(self, user, data):
        FanProfile.objects.create(
            user=user,
            verification_status=VerificationStatus.PENDING,
        )

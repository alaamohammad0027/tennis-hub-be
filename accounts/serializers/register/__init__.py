from .base import BaseRegisterSerializer
from .federation import FederationRegisterSerializer
from .club import ClubRegisterSerializer
from .coach import CoachRegisterSerializer
from .referee import RefereeRegisterSerializer
from .player import PlayerRegisterSerializer
from .fan import FanRegisterSerializer
from .otp import ResendVerificationSerializer, VerifyEmailSerializer
from .social import CompleteProfileSerializer
from accounts.models import UserProfileType

REGISTER_SERIALIZER_MAP = {
    UserProfileType.FEDERATION: FederationRegisterSerializer,
    UserProfileType.CLUB: ClubRegisterSerializer,
    UserProfileType.COACH: CoachRegisterSerializer,
    UserProfileType.REFEREE: RefereeRegisterSerializer,
    UserProfileType.PLAYER: PlayerRegisterSerializer,
    UserProfileType.FAN: FanRegisterSerializer,
}

__all__ = [
    "BaseRegisterSerializer",
    "FederationRegisterSerializer",
    "ClubRegisterSerializer",
    "CoachRegisterSerializer",
    "RefereeRegisterSerializer",
    "PlayerRegisterSerializer",
    "FanRegisterSerializer",
    "ResendVerificationSerializer",
    "VerifyEmailSerializer",
    "CompleteProfileSerializer",
    "REGISTER_SERIALIZER_MAP",
]

"""
accounts/serializers/profiles/

One serializer per profile type. Each exposes three field preset lists:

  ADMIN_FIELDS  — everything; default for admin callers
  PUBLIC_FIELDS — safe subset; used when a non-admin views related profiles
  ME_FIELDS     — admin fields minus `user`; used in GET /me

Usage:
  CoachProfileSerializer(instance, context=ctx)                              # admin
  CoachProfileSerializer(instance, fields=CoachProfileSerializer.PUBLIC_FIELDS, context=ctx)
  CoachProfileSerializer(instance, fields=CoachProfileSerializer.ME_FIELDS, context=ctx)
"""

from .base import UserSnapshotSerializer
from .federation import FederationProfileSerializer
from .club import ClubProfileSerializer
from .coach import CoachProfileSerializer
from .referee import RefereeProfileSerializer
from .player import PlayerProfileSerializer
from .fan import FanProfileSerializer

__all__ = [
    "UserSnapshotSerializer",
    "FederationProfileSerializer",
    "ClubProfileSerializer",
    "CoachProfileSerializer",
    "RefereeProfileSerializer",
    "PlayerProfileSerializer",
    "FanProfileSerializer",
]

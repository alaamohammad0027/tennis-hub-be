from rest_framework import serializers

from accounts.models import FanProfile
from accounts.serializers.profiles.base import UserSnapshotSerializer, SYSTEM_READ_ONLY
from core.services.serializers import DynamicFieldsModelSerializer

_ADMIN = [
    "id",
    "user",
    "favorite_club",
    "favorite_club_name",
    "verification_status",
    "is_active",
    "created_at",
    "updated_at",
]
_PUBLIC = [
    "id",
    "user",
    "favorite_club_name",
    "verification_status",
]
_ME = [f for f in _ADMIN if f != "user"]


class FanProfileSerializer(DynamicFieldsModelSerializer):
    user = UserSnapshotSerializer(read_only=True)
    favorite_club_name = serializers.CharField(
        source="favorite_club.club_name", read_only=True, default=None
    )

    ADMIN_FIELDS = _ADMIN
    PUBLIC_FIELDS = _PUBLIC
    ME_FIELDS = _ME

    class Meta:
        model = FanProfile
        fields = _ADMIN
        read_only_fields = SYSTEM_READ_ONLY

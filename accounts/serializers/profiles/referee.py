from accounts.models import RefereeProfile
from accounts.serializers.profiles.base import UserSnapshotSerializer, SYSTEM_READ_ONLY
from core.services.serializers import DynamicFieldsModelSerializer

_ADMIN = [
    "id",
    "user",
    "referee_level",
    "license_number",
    "certifications",
    "years_experience",
    "itf_badge",
    "verification_status",
    "verified_by",
    "verified_at",
    "rejection_reason",
    "is_active",
    "created_at",
    "updated_at",
]
_PUBLIC = [
    "id",
    "user",
    "referee_level",
    "years_experience",
    "itf_badge",
    "verification_status",
    "verified_at",
]
_ME = [f for f in _ADMIN if f != "user"]


class RefereeProfileSerializer(DynamicFieldsModelSerializer):
    user = UserSnapshotSerializer(read_only=True)

    ADMIN_FIELDS = _ADMIN
    PUBLIC_FIELDS = _PUBLIC
    ME_FIELDS = _ME

    class Meta:
        model = RefereeProfile
        fields = _ADMIN
        read_only_fields = SYSTEM_READ_ONLY

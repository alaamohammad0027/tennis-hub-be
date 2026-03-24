from accounts.models import CoachProfile
from accounts.serializers.profiles.base import UserSnapshotSerializer, SYSTEM_READ_ONLY
from core.services.serializers import DynamicFieldsModelSerializer

_ADMIN = [
    "id",
    "user",
    "specialization",
    "coaching_level",
    "license_number",
    "certifications",
    "years_experience",
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
    "specialization",
    "coaching_level",
    "years_experience",
    "verification_status",
    "verified_at",
]
_ME = [f for f in _ADMIN if f != "user"]


class CoachProfileSerializer(DynamicFieldsModelSerializer):
    user = UserSnapshotSerializer(read_only=True)

    ADMIN_FIELDS = _ADMIN
    PUBLIC_FIELDS = _PUBLIC
    ME_FIELDS = _ME

    class Meta:
        model = CoachProfile
        fields = _ADMIN
        read_only_fields = SYSTEM_READ_ONLY

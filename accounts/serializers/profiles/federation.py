from django_countries.serializer_fields import CountryField

from accounts.models import FederationProfile
from accounts.serializers.profiles.base import UserSnapshotSerializer, SYSTEM_READ_ONLY
from core.services.serializers import DynamicFieldsModelSerializer

_ADMIN = [
    "id",
    "user",
    "federation_name",
    "sport",
    "country",
    "founding_year",
    "registration_number",
    "logo",
    "website",
    "contact_email",
    "contact_phone",
    "description",
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
    "federation_name",
    "sport",
    "country",
    "founding_year",
    "logo",
    "website",
    "description",
    "verification_status",
    "verified_at",
]
_ME = [f for f in _ADMIN if f != "user"]


class FederationProfileSerializer(DynamicFieldsModelSerializer):
    user = UserSnapshotSerializer(read_only=True)
    country = CountryField(required=False, allow_blank=True)

    ADMIN_FIELDS = _ADMIN
    PUBLIC_FIELDS = _PUBLIC
    ME_FIELDS = _ME

    class Meta:
        model = FederationProfile
        fields = _ADMIN
        read_only_fields = SYSTEM_READ_ONLY

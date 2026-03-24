from rest_framework import serializers
from accounts.models.users import User
from core.services.serializers import DynamicFieldsModelSerializer


class UserSnapshotSerializer(serializers.ModelSerializer):
    """Minimal user info embedded inside a profile. Read-only."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "phone_number",
            "photo",
            "user_type",
            "nationality",
            "date_of_birth",
            "bio",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "email",
            "phone_number",
            "photo",
            "user_type",
            "nationality",
            "date_of_birth",
            "bio",
        ]


# Shared system-managed fields — always read-only on every profile
SYSTEM_READ_ONLY = [
    "id",
    "user",
    "verification_status",
    "verified_by",
    "verified_at",
    "rejection_reason",
    "is_active",
    "created_at",
    "updated_at",
]

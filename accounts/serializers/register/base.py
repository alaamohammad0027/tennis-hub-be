from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from accounts.models import User


class BaseRegisterSerializer(serializers.Serializer):
    """
    Base for all type-specific register serializers.

    USER_TYPE is NOT accepted from the request body — the endpoint URL
    determines the type (e.g. POST /register/coach/).

    Subclasses add type-specific profile fields directly (flat).
    """

    USER_TYPE = None

    # ── User fields ──────────────────────────────────────────
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True, default=""
    )
    nationality = CountryField(required=False, allow_blank=True, default="")
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords do not match.")}
            )
        return attrs

    def _create_user(self, data):
        return User.objects.create_user(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone_number=data.get("phone", ""),
            user_type=self.USER_TYPE,
            is_active=True,
            nationality=data.get("nationality", ""),
            date_of_birth=data.get("date_of_birth"),
            bio=data.get("bio", ""),
        )

    def _create_profile(self, user, data):
        raise NotImplementedError

    @transaction.atomic
    def save(self):
        data = self.validated_data
        user = self._create_user(data)
        self._create_profile(user, data)
        return user

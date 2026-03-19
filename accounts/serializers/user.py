from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from accounts.models.users import User, UserType
from core.services.serializers import DynamicFieldsModelSerializer
from core.services.validators import validate_image_only


class UserBaseSerializer(DynamicFieldsModelSerializer):
    """Base user serializer with common fields and validations"""

    full_name = serializers.CharField(read_only=True, source="get_full_name")

    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "is_active",
            "photo",
            "user_type",
        )
        read_only_fields = (
            "id",
            "full_name",
        )

    def validate_photo(self, value):
        return validate_image_only(value)


class UserCreateSerializer(UserBaseSerializer):
    """Serializer for creating users"""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ("password", "password_confirm")
        read_only_fields = UserBaseSerializer.Meta.read_only_fields + ("photo",)

    def validate_password(self, value):
        """Validate password using Django's validators"""
        validate_password(value)
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Password confirmation doesn't match password.")}
            )

        # Validate email uniqueness for CREATE
        email = attrs.get("email")
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": _("A user with this email already exists in the system.")}
            )

        return attrs

    def create(self, validated_data):
        """Create user with proper password hashing"""
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)
        return user


class ProfileSerializer(UserBaseSerializer):
    """Serializer for the authenticated user's own profile"""

    class Meta(UserBaseSerializer.Meta):
        read_only_fields = UserBaseSerializer.Meta.read_only_fields + (
            "email",
            "user_type",
            "is_active",
        )
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
        }


class UserUpdateSerializer(UserBaseSerializer):
    """Serializer for updating users (including optional password change)"""

    new_password = serializers.CharField(write_only=True, min_length=8, required=False)
    new_password_confirm = serializers.CharField(
        write_only=True, min_length=8, required=False
    )

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + (
            "new_password",
            "new_password_confirm",
        )
        read_only_fields = UserBaseSerializer.Meta.read_only_fields + ("photo",)
        extra_kwargs = {
            "email": {
                "required": False,
                "validators": [],  # Remove DRF's auto UniqueValidator
            }
        }

    def validate_new_password(self, value):
        """Validate new password if provided"""
        validate_password(value, user=self.instance)
        return value

    def validate(self, attrs):
        """Cross-field validation for password fields"""
        new_password = attrs.get("new_password")
        new_password_confirm = attrs.get("new_password_confirm")

        # If any password field is provided, all must be provided
        password_fields = [new_password, new_password_confirm]
        password_provided = any(password_fields)

        if password_provided and not all(password_fields):
            raise serializers.ValidationError(
                {
                    "password": _(
                        "To change password, provide new_password and new_password_confirm."
                    )
                }
            )

        if new_password and new_password != new_password_confirm:
            raise serializers.ValidationError(
                {
                    "new_password_confirm": _(
                        "Password confirmation doesn't match new password."
                    )
                }
            )

        # Validate email uniqueness for UPDATE (instance IS available in validate() method!)
        email = attrs.get("email")
        if email and self.instance:
            # Check if email changed
            if email != self.instance.email:
                if User.objects.filter(email=email).exists():
                    raise serializers.ValidationError(
                        {
                            "email": _(
                                "A user with this email already exists in the system."
                            )
                        }
                    )

        return attrs

    def update(self, instance, validated_data):
        """Update user with optional password change"""
        # Handle password update
        new_password = validated_data.pop("new_password", None)
        validated_data.pop("new_password_confirm", None)

        if new_password:
            instance.set_password(new_password)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

from rest_framework import serializers
from django.contrib import auth
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from typing import Any, Dict, Optional
from accounts.models.users import User


class UserTokenSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def to_representation(self, instance: User) -> Dict[str, str]:
        tokens = instance.tokens()

        return {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
        }


class LoginResponseSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    full_name = serializers.CharField(read_only=True, required=False)
    user_type = serializers.CharField(read_only=True, required=False)
    tokens = UserTokenSerializer(read_only=True, required=False)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        help_text=_("Email address must be a valid email format."),
    )

    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        validated_date = super().validate(attrs)
        email = validated_date.get("email")
        password = validated_date.get("password")
        user: Optional[User] = auth.authenticate(email=email, password=password)

        if not user:
            raise AuthenticationFailed(_("Invalid credentials"))
        elif not user.is_active:
            raise AuthenticationFailed(_("Account disabled"))

        validated_date["user"] = user
        return validated_date

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.validated_data.get("user")
        data["full_name"] = user.get_full_name()
        data["user_type"] = user.user_type
        data["tokens"] = UserTokenSerializer(user).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

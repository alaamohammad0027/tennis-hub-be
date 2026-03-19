from rest_framework import serializers
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework.exceptions import AuthenticationFailed
from accounts.models import User, OTP, OTPTypeChoices
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from typing import Dict, Any
from core.services.exceptions import CustomAPIException
import jwt
from django.conf import settings


class RequestResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset using email.
    """

    email = serializers.EmailField(
        required=True,
        help_text=_("Email address must be a valid email format."),
    )
    token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data["email"]
        user = User.objects.filter(email=email).first()
        validated_data["user"] = user
        return validated_data


class VerifyResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for verifying a password reset OTP using JWT token.
    """

    token = serializers.CharField(
        required=True,
        help_text=_("JWT token received during reset password request"),
        write_only=True,
    )
    otp = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6,
        help_text=_("6-digit OTP code"),
        write_only=True,
    )
    uidb64 = serializers.CharField(read_only=True)
    reset_token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        jwt_token = validated_data.get("token")
        otp = validated_data.get("otp")

        try:
            payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id)
        except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
            raise CustomAPIException(
                detail=_("Invalid or expired token"),
                code="INVALID_TOKEN",
            )

        if not OTP.verify_otp(user.email, otp, OTPTypeChoices.RESET_PASSWORD):
            raise CustomAPIException(
                detail=_("Invalid OTP"),
                code="INVALID_OTP",
            )

        validated_data["user"] = user
        return validated_data


class SetNewPasswordSerializer(serializers.Serializer):
    """
    Serializer for setting a new password using a reset token.
    """

    password = serializers.CharField(
        write_only=True, required=True, help_text=_("New password")
    )
    uidb64 = serializers.CharField(
        write_only=True,
        required=True,
    )
    token = serializers.CharField(
        write_only=True,
        required=True,
    )

    def check_new_password(self, value: str, user: User) -> None:
        """
        Validate the password using Django's password validators.
        """
        try:
            validate_password(value, user)
        except Exception as e:
            raise serializers.ValidationError(list(e.messages))

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        validated_data = super().validate(attrs)
        try:
            uid = force_str(urlsafe_base64_decode(validated_data.get("uidb64")))
            user = User.objects.get(id=uid)

            # Validate password
            self.check_new_password(validated_data.get("password"), user)

            if not PasswordResetTokenGenerator().check_token(
                user, validated_data.get("token")
            ):
                raise AuthenticationFailed(
                    _("The reset link is invalid or has expired."), 401
                )

            # Set new password
            user.set_password(validated_data.get("password"))
            user.save(update_fields=["password"])

            validated_data["user"] = user
            return validated_data
        except (User.DoesNotExist, TypeError, ValueError, OverflowError):
            raise AuthenticationFailed(
                _("The reset link is invalid or has expired."), 401
            )

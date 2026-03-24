from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from accounts.models import User, OTPTypeChoices


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower()


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        from accounts.models.otp import OTP

        email = attrs["email"].lower()
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"email": _("No account found.")})
        if user.email_verified:
            raise serializers.ValidationError({"email": _("Account already verified.")})
        if not OTP.verify_otp(
            email, attrs["otp_code"], OTPTypeChoices.EMAIL_VERIFICATION
        ):
            raise serializers.ValidationError(
                {"otp_code": _("Invalid or expired OTP.")}
            )
        attrs["user"] = user
        return attrs

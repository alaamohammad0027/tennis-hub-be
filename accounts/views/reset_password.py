import datetime
import jwt
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status, permissions
from rest_framework.response import Response

from accounts.models import OTPTypeChoices
from accounts.serializers.reset_password import (
    RequestResetPasswordSerializer,
    VerifyResetPasswordSerializer,
    SetNewPasswordSerializer,
)
from accounts.views.schema import (
    request_reset_schema,
    verify_reset_schema,
    set_new_password_schema,
)
from core.services.email import OTPService
from core.services.exceptions import CustomAPIException

GENERIC_RESET_MESSAGE = _(
    "If this email is registered, you will receive a password reset code."
)


@request_reset_schema
class RequestPasswordReset(generics.GenericAPIView):
    serializer_class = RequestResetPasswordSerializer
    permission_classes = [permissions.AllowAny]
    otp_service = OTPService()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        email = serializer.validated_data["email"]

        if not user:
            return Response(
                {"email": email, "message": GENERIC_RESET_MESSAGE},
                status=status.HTTP_200_OK,
            )

        is_sent, message = self.otp_service.generate_otp(
            user.email, OTPTypeChoices.RESET_PASSWORD
        )
        if not is_sent:
            raise CustomAPIException(detail=message, code="OTP_SEND_FAILED")

        jwt_token = jwt.encode(
            {
                "user_id": str(user.id),
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(minutes=15),
                "type": "password_reset",
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        return Response(
            {"email": user.email, "token": jwt_token},
            status=status.HTTP_200_OK,
        )


@verify_reset_schema
class VerifyPasswordReset(generics.GenericAPIView):
    serializer_class = VerifyResetPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        reset_token = PasswordResetTokenGenerator().make_token(user)

        return Response(
            {"uidb64": uidb64, "reset_token": reset_token},
            status=status.HTTP_200_OK,
        )


@set_new_password_schema
class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"message": _("Password reset successful")},
            status=status.HTTP_200_OK,
        )

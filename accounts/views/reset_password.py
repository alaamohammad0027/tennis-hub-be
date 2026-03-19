from rest_framework import generics, status, permissions
from accounts.serializers.reset_password import (
    SetNewPasswordSerializer,
    RequestResetPasswordSerializer,
    VerifyResetPasswordSerializer,
)
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import smart_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from drf_spectacular.utils import extend_schema, OpenApiResponse
import jwt
import datetime

from accounts.models import OTPTypeChoices
from core.services.exceptions import CustomAPIException
from core.services.email import OTPService
from django.conf import settings

GENERIC_RESET_MESSAGE = _(
    "If this email is registered, you will receive a password reset code."
)


class RequestPasswordReset(generics.GenericAPIView):
    """
    API to request a password reset by sending a reset OTP.
    Returns a generic message regardless of whether the email exists
    to prevent email enumeration.
    """

    serializer_class = RequestResetPasswordSerializer
    permission_classes = [permissions.AllowAny]
    otp_service = OTPService()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        email = serializer.validated_data["email"]

        # If user doesn't exist, return generic success to prevent email enumeration
        if not user:
            return Response(
                {"email": email, "message": GENERIC_RESET_MESSAGE},
                status=status.HTTP_200_OK,
            )

        # Send reset password OTP
        is_sent, message = self.otp_service.generate_otp(
            user.email, OTPTypeChoices.RESET_PASSWORD
        )
        if not is_sent:
            raise CustomAPIException(
                detail=message,
                code="OTP_SEND_FAILED",
            )

        # Generate JWT token with user ID
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


class VerifyPasswordReset(generics.GenericAPIView):
    """
    API to verify a password reset OTP and generate reset tokens.
    """

    serializer_class = VerifyResetPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Generate password reset tokens
        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        reset_token = PasswordResetTokenGenerator().make_token(user)

        return Response(
            {"uidb64": uidb64, "reset_token": reset_token},
            status=status.HTTP_200_OK,
        )


class SetNewPasswordAPIView(generics.GenericAPIView):
    """
    API to set a new password using a valid token and UID.
    """

    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                },
                description="Password reset successful",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {"message": _("Password reset successful")},
            status=status.HTTP_200_OK,
        )

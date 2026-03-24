from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import OTPTypeChoices
from accounts.serializers import (
    FederationRegisterSerializer,
    ClubRegisterSerializer,
    CoachRegisterSerializer,
    RefereeRegisterSerializer,
    PlayerRegisterSerializer,
    FanRegisterSerializer,
    ResendVerificationSerializer,
    VerifyEmailSerializer,
    CompleteProfileSerializer,
)
from accounts.serializers.authentication import UserTokenSerializer
from accounts.views.schema import (
    federation_register_schema,
    club_register_schema,
    coach_register_schema,
    referee_register_schema,
    player_register_schema,
    fan_register_schema,
    resend_verification_schema,
    verify_email_schema,
    complete_profile_schema,
)
from core.services.email import OTPService
from core.services.exceptions import CustomAPIException

_otp_service = OTPService()


# ─────────────────────────────────────────────────────────────
# Shared base — OTP flow
# ─────────────────────────────────────────────────────────────


class _RegisterBase(APIView):
    permission_classes = [AllowAny]
    serializer_class = None

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        is_sent, message = _otp_service.generate_otp(
            user.email, OTPTypeChoices.EMAIL_VERIFICATION
        )
        if not is_sent:
            user.delete()
            raise CustomAPIException(detail=message, code="OTP_SEND_FAILED")

        return Response(
            {
                "email": user.email,
                "message": _(
                    "Registration successful. Please check your email for the verification code."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────
# Per-type views
# ─────────────────────────────────────────────────────────────


@federation_register_schema
class FederationRegisterView(_RegisterBase):
    serializer_class = FederationRegisterSerializer


@club_register_schema
class ClubRegisterView(_RegisterBase):
    serializer_class = ClubRegisterSerializer


@coach_register_schema
class CoachRegisterView(_RegisterBase):
    serializer_class = CoachRegisterSerializer


@referee_register_schema
class RefereeRegisterView(_RegisterBase):
    serializer_class = RefereeRegisterSerializer


@player_register_schema
class PlayerRegisterView(_RegisterBase):
    serializer_class = PlayerRegisterSerializer


@fan_register_schema
class FanRegisterView(_RegisterBase):
    serializer_class = FanRegisterSerializer


# ─────────────────────────────────────────────────────────────
# Resend verification OTP
# ─────────────────────────────────────────────────────────────


@resend_verification_schema
class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        from accounts.models import User

        user = User.objects.filter(email=email).first()

        # Generic response to avoid user enumeration
        if not user or user.email_verified:
            return Response(
                {
                    "message": _(
                        "If this email is registered and unverified, a new code has been sent."
                    )
                },
                status=status.HTTP_200_OK,
            )

        is_sent, message = _otp_service.generate_otp(
            user.email, OTPTypeChoices.EMAIL_VERIFICATION
        )
        if not is_sent:
            raise CustomAPIException(detail=message, code="OTP_SEND_FAILED")

        return Response(
            {
                "email": user.email,
                "message": _("Verification code resent. Please check your email."),
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────
# Verify email
# ─────────────────────────────────────────────────────────────


@verify_email_schema
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        user.email_verified = True
        user.save(update_fields=["email_verified"])

        from accounts.models.profiles.base import VerificationStatus

        for attr in (
            "federation_profile",
            "club_profile",
            "coach_profile",
            "referee_profile",
            "player_profile",
        ):
            profile = getattr(user, attr, None)
            if profile and profile.verification_status == VerificationStatus.PENDING:
                profile.verification_status = VerificationStatus.UNDER_REVIEW
                profile.save(update_fields=["verification_status"])
                break

        return Response(
            {
                "email": user.email,
                "full_name": user.get_full_name(),
                "user_type": user.user_type,
                "tokens": UserTokenSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────
# Complete profile (Google OAuth new users)
# ─────────────────────────────────────────────────────────────


@complete_profile_schema
class CompleteProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CompleteProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(
            {"message": _("Profile completed successfully.")},
            status=status.HTTP_201_CREATED,
        )

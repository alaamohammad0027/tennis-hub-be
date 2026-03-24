from django.conf import settings
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from core.services.exceptions import CustomAPIException


def verify_google_token(id_token_str: str) -> dict:
    """
    Verifies a Google ID token and returns the payload.
    Requires: pip install google-auth
    Settings: GOOGLE_CLIENT_ID
    """
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
    except ImportError:
        raise CustomAPIException(
            detail="google-auth package not installed.",
            code="GOOGLE_AUTH_NOT_INSTALLED",
        )

    try:
        payload = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        return payload
    except ValueError as e:
        raise CustomAPIException(
            detail=_("Invalid Google token."),
            code="INVALID_GOOGLE_TOKEN",
        )


@extend_schema(
    tags=["Authentication"],
    description=(
        "Sign in with Google. Pass the Google ID token from the frontend. "
        "Returns JWT tokens + `is_new_user` flag. "
        "If `is_new_user=true`, redirect the user to POST /complete-profile."
    ),
)
class GoogleOAuthView(APIView):
    """
    POST /apis/auth/social/google
    Accepts Google ID token from the frontend (after Google Sign-In).
    Creates user if new, logs in if existing.

    Flow:
      - New user  → is_active=True (Google already verified email)
                  → returns { tokens, is_new_user: true }
                  → frontend redirects to /complete-profile

      - Existing  → returns { tokens, is_new_user: false }

    Requires settings.GOOGLE_CLIENT_ID
    """

    permission_classes = [AllowAny]

    def post(self, request):
        id_token_str = request.data.get("id_token")
        if not id_token_str:
            raise CustomAPIException(
                detail=_("id_token is required."),
                code="MISSING_TOKEN",
            )

        payload = verify_google_token(id_token_str)

        email = payload.get("email", "").lower()
        first_name = payload.get("given_name", "")
        last_name = payload.get("family_name", "")
        google_sub = payload.get("sub", "")  # unique Google user ID

        if not email:
            raise CustomAPIException(
                detail=_("Google account has no email."),
                code="NO_EMAIL",
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "email_verified": True,  # Google already verified the email
            },
        )

        # Determine if user has completed their tennis profile
        has_profile = any(
            hasattr(user, attr)
            for attr in (
                "federation_profile",
                "club_profile",
                "coach_profile",
                "referee_profile",
                "player_profile",
                "fan_profile",
            )
        )

        tokens = user.tokens()
        return Response(
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "is_new_user": created or not has_profile,
                "profile_complete": has_profile,
            },
            status=status.HTTP_200_OK,
        )

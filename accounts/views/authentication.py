from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.serializers import (
    LogoutSerializer,
    LoginSerializer,
    LoginResponseSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from core.services.exceptions import CustomAPIException
from django.utils import timezone


class LoginAPIView(APIView):
    """
    Login user with email and password
    Permissions: AllowAny
    """

    permission_classes = [permissions.AllowAny]

    def get_serializer(self, *args, **kwargs):
        return LoginSerializer(*args, **kwargs)

    @extend_schema(
        description="Login user with email and password",
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        # update last login date of user
        user = serializer.validated_data["user"]
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutAPIView(generics.GenericAPIView):
    """
    Logout user and blacklist the refresh token
    Permissions: IsAuthenticated
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        return LogoutSerializer(*args, **kwargs)

    @extend_schema(
        description="Logout user and blacklist the refresh token",
        responses={200: "{'message': 'Logged out successfully'}"},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get("refresh")

        try:
            # Blacklist the refresh token
            RefreshToken(refresh_token).blacklist()
            return Response(
                {"message": _("Logged out successfully.")}, status=status.HTTP_200_OK
            )

        except Exception:
            raise CustomAPIException(
                detail=_("Logout failed"),
                code="LOGOUT_FAILED",
            )

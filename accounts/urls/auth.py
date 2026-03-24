from django.urls import path

from accounts.views.authentication import LoginAPIView, LogoutAPIView
from accounts.views.refresh_token import CustomRefreshTokenAPIView
from accounts.views.reset_password import (
    RequestPasswordReset,
    VerifyPasswordReset,
    SetNewPasswordAPIView,
)
from accounts.views.me import MeAPIView
from accounts.views.social_auth import GoogleOAuthView

urlpatterns = [
    path("login", LoginAPIView.as_view(), name="login"),
    path("logout", LogoutAPIView.as_view(), name="logout"),
    path("token/refresh", CustomRefreshTokenAPIView.as_view(), name="token_refresh"),
    # Social
    path("social/google", GoogleOAuthView.as_view(), name="social_google"),
    # Password reset
    path(
        "password/request-reset",
        RequestPasswordReset.as_view(),
        name="request_reset_password",
    ),
    path(
        "password/verify-reset",
        VerifyPasswordReset.as_view(),
        name="verify_reset_password",
    ),
    path(
        "password/reset-complete",
        SetNewPasswordAPIView.as_view(),
        name="password_reset_complete",
    ),
    path("me", MeAPIView.as_view(), name="me"),
]

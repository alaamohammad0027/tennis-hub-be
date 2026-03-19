from accounts.views.authentication import LoginAPIView, LogoutAPIView
from accounts.views.reset_password import (
    RequestPasswordReset,
    VerifyPasswordReset,
    SetNewPasswordAPIView,
)
from accounts.views.refresh_token import CustomRefreshTokenAPIView
from accounts.views.users import UserViewSet
from accounts.views.profile import ProfileAPIView
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("login", LoginAPIView.as_view(), name="login"),
    path("logout", LogoutAPIView.as_view(), name="logout"),
    path(
        "token/refresh",
        CustomRefreshTokenAPIView.as_view(),
        name="token_refresh",
    ),
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
    path("profile", ProfileAPIView.as_view(), name="profile"),
    path("", include(router.urls)),
]

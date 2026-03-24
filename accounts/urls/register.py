from django.urls import path

from accounts.views.register import (
    FederationRegisterView,
    ClubRegisterView,
    CoachRegisterView,
    RefereeRegisterView,
    PlayerRegisterView,
    FanRegisterView,
    ResendVerificationView,
    VerifyEmailView,
    CompleteProfileView,
)

urlpatterns = [
    path(
        "register/federation",
        FederationRegisterView.as_view(),
        name="register_federation",
    ),
    path("register/club", ClubRegisterView.as_view(), name="register_club"),
    path("register/coach", CoachRegisterView.as_view(), name="register_coach"),
    path("register/referee", RefereeRegisterView.as_view(), name="register_referee"),
    path("register/player", PlayerRegisterView.as_view(), name="register_player"),
    path("register/fan", FanRegisterView.as_view(), name="register_fan"),
    path(
        "resend-verification",
        ResendVerificationView.as_view(),
        name="resend_verification",
    ),
    path("verify-email", VerifyEmailView.as_view(), name="verify_email"),
    path("complete-profile", CompleteProfileView.as_view(), name="complete_profile"),
]

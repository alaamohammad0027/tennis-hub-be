from django.urls import path
from rest_framework.routers import DefaultRouter

from accounts.views.profiles import (
    FederationProfileViewSet,
    ClubProfileViewSet,
    CoachProfileViewSet,
    RefereeProfileViewSet,
    PlayerProfileViewSet,
    FanProfileViewSet,
)
from accounts.views.users import UserViewSet
from management.views.users import AdminUserViewSet, ChangeRoleView, CreateAdminView

router = DefaultRouter()

# Users
router.register(r"users", UserViewSet, basename="mgmt-user")
router.register(r"admin/users", AdminUserViewSet, basename="mgmt-admin-user")

# Profiles / Verification
router.register(
    r"federation-profiles", FederationProfileViewSet, basename="mgmt-federation-profile"
)
router.register(r"club-profiles", ClubProfileViewSet, basename="mgmt-club-profile")
router.register(r"coach-profiles", CoachProfileViewSet, basename="mgmt-coach-profile")
router.register(
    r"referee-profiles", RefereeProfileViewSet, basename="mgmt-referee-profile"
)
router.register(
    r"player-profiles", PlayerProfileViewSet, basename="mgmt-player-profile"
)
router.register(r"fan-profiles", FanProfileViewSet, basename="mgmt-fan-profile")

urlpatterns = router.urls + [
    path(
        "admin/users/create-admin/", CreateAdminView.as_view(), name="mgmt-create-admin"
    ),
    path(
        "admin/users/<uuid:pk>/change-role/",
        ChangeRoleView.as_view(),
        name="mgmt-change-role",
    ),
]

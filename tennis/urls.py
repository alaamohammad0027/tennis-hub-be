from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tennis.views import (
    AffiliationViewSet,
    TrainingLocationViewSet,
    GroupViewSet,
    GroupMembershipViewSet,
    GroupNoteViewSet,
    PlayerSearchView,
    CalendarView,
    SessionViewSet,
    SessionAttendanceViewSet,
    SessionNoteViewSet,
)

router = DefaultRouter()

# Affiliations (unified)
router.register(r"affiliations", AffiliationViewSet, basename="affiliations")

# Locations
router.register(r"locations", TrainingLocationViewSet, basename="locations")

# Groups
router.register(r"groups", GroupViewSet, basename="groups")
router.register(
    r"group-memberships", GroupMembershipViewSet, basename="group-memberships"
)
router.register(r"group-notes", GroupNoteViewSet, basename="group-notes")

# Sessions
router.register(r"sessions", SessionViewSet, basename="sessions")
router.register(
    r"session-attendance", SessionAttendanceViewSet, basename="session-attendance"
)
router.register(r"session-notes", SessionNoteViewSet, basename="session-notes")

urlpatterns = [
    path("", include(router.urls)),
    path("player-search/", PlayerSearchView.as_view(), name="player-search"),
    path("calendar/", CalendarView.as_view(), name="calendar"),
]

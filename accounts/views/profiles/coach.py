from rest_framework.decorators import action

from accounts.models import CoachProfile
from accounts.models.choices import UserType
from accounts.serializers import CoachProfileSerializer
from accounts.filters import CoachProfileFilter
from accounts.views.profiles.base import _ProfileBase
from accounts.views.schema import coach_profiles_schema


@coach_profiles_schema
class CoachProfileViewSet(_ProfileBase):
    serializer_class = CoachProfileSerializer
    filterset_class = CoachProfileFilter
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "specialization",
    ]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == UserType.ADMIN:
            return CoachProfile.objects.select_related("user", "verified_by").order_by(
                "-created_at"
            )

        qs = CoachProfile.objects.select_related("user", "verified_by").filter(
            user=user
        )
        if user.user_type == UserType.CLUB:
            from tennis.models import Affiliation, AffiliationLinkType

            coach_user_ids = Affiliation.objects.filter(
                target=user,
                link_type=AffiliationLinkType.COACH_CLUB,
            ).values_list("requester_id", flat=True)
            qs = (
                qs | CoachProfile.objects.filter(user__id__in=coach_user_ids)
            ).distinct()
        return qs

    def _can_verify(self, request, profile):
        if request.user.user_type == UserType.ADMIN:
            return True
        if request.user.user_type == UserType.CLUB:
            from tennis.models import Affiliation, AffiliationLinkType

            return Affiliation.objects.filter(
                target=request.user,
                requester=profile.user,
                link_type=AffiliationLinkType.COACH_CLUB,
            ).exists()
        return False

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._do_approve(request, pk)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._do_reject(request, pk)

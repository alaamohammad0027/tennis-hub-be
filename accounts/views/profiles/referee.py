from rest_framework.decorators import action

from accounts.models import RefereeProfile
from accounts.models.choices import UserType
from accounts.serializers import RefereeProfileSerializer
from accounts.filters import RefereeProfileFilter
from accounts.views.profiles.base import _ProfileBase
from accounts.views.schema import referee_profiles_schema


@referee_profiles_schema
class RefereeProfileViewSet(_ProfileBase):
    serializer_class = RefereeProfileSerializer
    filterset_class = RefereeProfileFilter
    search_fields = ["user__first_name", "user__last_name", "user__email"]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == UserType.ADMIN:
            return RefereeProfile.objects.select_related(
                "user", "verified_by"
            ).order_by("-created_at")

        qs = RefereeProfile.objects.select_related("user", "verified_by").filter(
            user=user
        )
        if user.user_type == UserType.CLUB:
            from tennis.models import Affiliation, AffiliationLinkType

            referee_user_ids = Affiliation.objects.filter(
                target=user,
                link_type=AffiliationLinkType.REFEREE_CLUB,
            ).values_list("requester_id", flat=True)
            qs = (
                qs | RefereeProfile.objects.filter(user__id__in=referee_user_ids)
            ).distinct()
        elif user.user_type == UserType.FEDERATION:
            from tennis.models import Affiliation, AffiliationLinkType

            referee_user_ids = Affiliation.objects.filter(
                target=user,
                link_type=AffiliationLinkType.REFEREE_FEDERATION,
            ).values_list("requester_id", flat=True)
            qs = (
                qs | RefereeProfile.objects.filter(user__id__in=referee_user_ids)
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
                link_type=AffiliationLinkType.REFEREE_CLUB,
            ).exists()
        if request.user.user_type == UserType.FEDERATION:
            from tennis.models import Affiliation, AffiliationLinkType

            return Affiliation.objects.filter(
                target=request.user,
                requester=profile.user,
                link_type=AffiliationLinkType.REFEREE_FEDERATION,
            ).exists()
        return False

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._do_approve(request, pk)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._do_reject(request, pk)

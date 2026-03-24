from rest_framework.decorators import action

from accounts.models import ClubProfile
from accounts.models.choices import UserType
from accounts.serializers import ClubProfileSerializer
from accounts.filters import ClubProfileFilter
from accounts.views.profiles.base import _ProfileBase
from accounts.views.schema import club_profiles_schema


@club_profiles_schema
class ClubProfileViewSet(_ProfileBase):
    serializer_class = ClubProfileSerializer
    filterset_class = ClubProfileFilter
    search_fields = ["club_name", "city", "user__email"]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == UserType.ADMIN:
            return ClubProfile.objects.select_related("user", "verified_by").order_by(
                "club_name"
            )

        qs = ClubProfile.objects.select_related("user", "verified_by").filter(user=user)
        if user.user_type == UserType.FEDERATION:
            from tennis.models import Affiliation, AffiliationLinkType

            linked_user_ids = Affiliation.objects.filter(
                target=user,
                link_type=AffiliationLinkType.CLUB_FEDERATION,
            ).values_list("requester_id", flat=True)
            qs = (
                qs | ClubProfile.objects.filter(user__id__in=linked_user_ids)
            ).distinct()
        return qs

    def _can_verify(self, request, profile):
        return request.user.user_type == UserType.ADMIN or hasattr(
            request.user, "federation_profile"
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._do_approve(request, pk)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._do_reject(request, pk)

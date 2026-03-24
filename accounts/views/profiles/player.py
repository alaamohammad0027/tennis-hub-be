from rest_framework.decorators import action

from accounts.models import PlayerProfile
from accounts.models.choices import UserType
from accounts.serializers import PlayerProfileSerializer
from accounts.filters import PlayerProfileFilter
from accounts.views.profiles.base import _ProfileBase
from accounts.views.schema import player_profiles_schema


@player_profiles_schema
class PlayerProfileViewSet(_ProfileBase):
    serializer_class = PlayerProfileSerializer
    filterset_class = PlayerProfileFilter
    search_fields = ["user__first_name", "user__last_name", "user__email"]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == UserType.ADMIN:
            return PlayerProfile.objects.select_related("user", "verified_by").order_by(
                "-created_at"
            )

        qs = PlayerProfile.objects.select_related("user", "verified_by").filter(
            user=user
        )
        if user.user_type == UserType.CLUB:
            from tennis.models import Affiliation, AffiliationLinkType

            player_user_ids = Affiliation.objects.filter(
                target=user,
                link_type=AffiliationLinkType.PLAYER_CLUB,
            ).values_list("requester_id", flat=True)
            qs = (
                qs | PlayerProfile.objects.filter(user__id__in=player_user_ids)
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
                link_type=AffiliationLinkType.PLAYER_CLUB,
            ).exists()
        return False

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._do_approve(request, pk)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._do_reject(request, pk)

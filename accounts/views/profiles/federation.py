from rest_framework.decorators import action

from accounts.models import FederationProfile
from accounts.models.choices import UserType
from accounts.serializers import FederationProfileSerializer
from accounts.filters import FederationProfileFilter
from accounts.views.profiles.base import _ProfileBase
from accounts.views.schema import federation_profiles_schema


@federation_profiles_schema
class FederationProfileViewSet(_ProfileBase):
    serializer_class = FederationProfileSerializer
    filterset_class = FederationProfileFilter
    search_fields = [
        "federation_name",
        "user__email",
        "user__first_name",
        "user__last_name",
    ]

    def get_queryset(self):
        user = self.request.user
        qs = FederationProfile.objects.select_related("user", "verified_by")
        if user.user_type != UserType.ADMIN:
            qs = qs.filter(user=user)
        return qs.order_by("federation_name")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._do_approve(request, pk)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._do_reject(request, pk)

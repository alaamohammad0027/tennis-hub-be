from accounts.models import FanProfile
from accounts.models.choices import UserType
from accounts.serializers import FanProfileSerializer
from accounts.filters import FanProfileFilter
from accounts.views.profiles.base import _ProfileBase
from accounts.views.schema import fan_profiles_schema


@fan_profiles_schema
class FanProfileViewSet(_ProfileBase):
    serializer_class = FanProfileSerializer
    filterset_class = FanProfileFilter
    search_fields = ["user__first_name", "user__last_name", "user__email"]

    def get_queryset(self):
        user = self.request.user
        qs = FanProfile.objects.select_related("user", "favorite_club")
        if user.user_type != UserType.ADMIN:
            qs = qs.filter(user=user)
        return qs.order_by("-created_at")

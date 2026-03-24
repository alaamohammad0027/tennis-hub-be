import django_filters as filters
from django_countries import countries

from accounts.models import (
    User,
    FederationProfile,
    ClubProfile,
    CoachProfile,
    RefereeProfile,
    PlayerProfile,
    FanProfile,
)
from accounts.models.choices import UserType
from accounts.models.profiles.base import VerificationStatus


class UserFilter(filters.FilterSet):
    user_type = filters.ChoiceFilter(choices=UserType.choices)
    is_active = filters.BooleanFilter()
    email_verified = filters.BooleanFilter()

    class Meta:
        model = User
        fields = ["user_type", "is_active", "email_verified"]


class _VerificationFilterBase(filters.FilterSet):
    verification_status = filters.ChoiceFilter(choices=VerificationStatus.choices)
    is_active = filters.BooleanFilter()


class FederationProfileFilter(_VerificationFilterBase):
    country = filters.ChoiceFilter(choices=list(countries))
    sport = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = FederationProfile
        fields = ["verification_status", "is_active", "country", "sport"]


class ClubProfileFilter(_VerificationFilterBase):
    country = filters.ChoiceFilter(choices=list(countries))
    club_type = filters.CharFilter()
    city = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = ClubProfile
        fields = ["verification_status", "is_active", "country", "club_type", "city"]


class CoachProfileFilter(_VerificationFilterBase):
    coaching_level = filters.CharFilter()

    class Meta:
        model = CoachProfile
        fields = ["verification_status", "is_active", "coaching_level"]


class RefereeProfileFilter(_VerificationFilterBase):
    referee_level = filters.CharFilter()

    class Meta:
        model = RefereeProfile
        fields = ["verification_status", "is_active", "referee_level"]


class PlayerProfileFilter(_VerificationFilterBase):
    skill_level = filters.CharFilter()
    nationality = filters.ChoiceFilter(choices=list(countries))

    class Meta:
        model = PlayerProfile
        fields = ["verification_status", "is_active", "skill_level", "nationality"]


class FanProfileFilter(filters.FilterSet):
    is_active = filters.BooleanFilter()
    nationality = filters.ChoiceFilter(choices=list(countries))

    class Meta:
        model = FanProfile
        fields = ["is_active", "nationality"]

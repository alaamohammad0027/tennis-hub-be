import django_filters as filters

from tennis.models import (
    Affiliation,
    AffiliationStatus,
    AffiliationLinkType,
    Group,
    GroupStatus,
    GroupMembership,
    GroupNote,
    Session,
    SessionAttendance,
    SessionNote,
    SessionStatus,
    AttendanceStatus,
    PaymentStatus,
)


class AffiliationFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=AffiliationStatus.choices)
    link_type = filters.ChoiceFilter(choices=AffiliationLinkType.choices)
    requester = filters.UUIDFilter(field_name="requester__id")
    target = filters.UUIDFilter(field_name="target__id")
    role = filters.CharFilter()

    class Meta:
        model = Affiliation
        fields = ["status", "link_type", "requester", "target", "role"]


# ─── Coaching ─────────────────────────────────────────────────


class GroupFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=GroupStatus.choices)
    club = filters.UUIDFilter(field_name="club__id")
    coach = filters.UUIDFilter(field_name="coach__id")

    class Meta:
        model = Group
        fields = ["status", "club", "coach"]


class GroupMembershipFilter(filters.FilterSet):
    group = filters.UUIDFilter(field_name="group__id")
    player = filters.UUIDFilter(field_name="player__id")
    is_active = filters.BooleanFilter()

    class Meta:
        model = GroupMembership
        fields = ["group", "player", "is_active"]


class GroupNoteFilter(filters.FilterSet):
    group = filters.UUIDFilter(field_name="group__id")
    player = filters.UUIDFilter(field_name="player__id")

    class Meta:
        model = GroupNote
        fields = ["group", "player"]


# ─── Sessions ─────────────────────────────────────────────────


class SessionFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=SessionStatus.choices)
    payment_status = filters.ChoiceFilter(choices=PaymentStatus.choices)
    group = filters.UUIDFilter(field_name="group__id")
    coach = filters.UUIDFilter(field_name="coach__id")
    date = filters.DateFilter()
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Session
        fields = [
            "status",
            "payment_status",
            "group",
            "coach",
            "date",
            "date_from",
            "date_to",
        ]


class SessionAttendanceFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=AttendanceStatus.choices)
    session = filters.UUIDFilter(field_name="session__id")
    player = filters.UUIDFilter(field_name="player__id")

    class Meta:
        model = SessionAttendance
        fields = ["status", "session", "player"]


class SessionNoteFilter(filters.FilterSet):
    session = filters.UUIDFilter(field_name="session__id")

    class Meta:
        model = SessionNote
        fields = ["session"]

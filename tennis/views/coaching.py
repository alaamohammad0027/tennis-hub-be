from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import PlayerProfile
from accounts.models.choices import UserType
from tennis.filters import GroupFilter, GroupMembershipFilter, GroupNoteFilter
from tennis.models import (
    TrainingLocation,
    Group,
    GroupStatus,
    GroupMembership,
    GroupNote,
    AffiliationStatus,
    AttendanceStatus,
    Session,
    SessionAttendance,
)
from tennis.serializers import (
    TrainingLocationSerializer,
    GroupSerializer,
    GroupMembershipSerializer,
    GroupNoteSerializer,
    PlayerSearchResultSerializer,
    AddPlayerToGroupSerializer,
    SessionSerializer,
)
from tennis.permissions import IsAdmin, IsAdminOrCoach, IsAdminOrClub

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        tags=["Tennis - Locations"],
        summary="List training locations",
        description="Returns all active training locations (courts, facilities). Available to all authenticated users.",
    ),
    retrieve=extend_schema(
        tags=["Tennis - Locations"], summary="Get a training location"
    ),
    create=extend_schema(
        tags=["Tennis - Locations"],
        summary="Create a training location",
        description="**Who can create:** Admin or Club users only.",
    ),
    update=extend_schema(
        tags=["Tennis - Locations"],
        summary="Update a training location",
        description="**Who can update:** Admin or Club users only.",
    ),
    partial_update=extend_schema(
        tags=["Tennis - Locations"],
        summary="Partially update a training location",
        description="**Who can update:** Admin or Club users only.",
    ),
    destroy=extend_schema(
        tags=["Tennis - Locations"],
        summary="Delete a training location",
        description="**Who can delete:** Admin or Club users only.",
    ),
)
class TrainingLocationViewSet(viewsets.ModelViewSet):
    queryset = TrainingLocation.objects.filter(is_active=True).order_by("name")
    serializer_class = TrainingLocationSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminOrClub()]
        return [IsAuthenticated()]


@extend_schema_view(
    list=extend_schema(
        tags=["Tennis - Groups"],
        summary="List training groups",
        description=(
            "Returns coaching groups.\n\n"
            "**Who sees what:**\n"
            "- **Club user** → groups belonging to their club\n"
            "- **Coach user** → groups they are assigned to\n"
            "- **Player user** → groups they are a member of\n"
            "- **Admin** → all groups\n"
            "- **Other users** → groups they created\n\n"
            "**Filters:** `?status=active|closed|archived`, `?club=<uuid>`, `?coach=<uuid>`"
        ),
    ),
    retrieve=extend_schema(tags=["Tennis - Groups"], summary="Get a training group"),
    create=extend_schema(
        tags=["Tennis - Groups"],
        summary="Create a training group",
        description=(
            "**Who can create:** Any authenticated user.\n\n"
            "**Auto-assignment rules:**\n"
            "- **Coach** → `coach` defaults to your own profile; you cannot assign a different coach.\n"
            "- **Club** → `club` is auto-set to your club; you can assign any coach "
            "with an active affiliation with your club.\n"
            "- **Admin** → full control over `coach` and `club`.\n"
            "- **Everyone else** → `coach` and `club` are optional (personal/friend group).\n\n"
            "**Location:** Use `location` (FK to a TrainingLocation) **or** `location_manual` "
            "(free-text address). Both are optional."
        ),
    ),
    update=extend_schema(
        tags=["Tennis - Groups"],
        summary="Update a training group",
        description="**Who can update:** Admin, the assigned Coach, or the linked Club.",
    ),
    partial_update=extend_schema(
        tags=["Tennis - Groups"],
        summary="Partially update a training group",
        description="**Who can update:** Admin, the assigned Coach, or the linked Club.",
    ),
    destroy=extend_schema(
        tags=["Tennis - Groups"],
        summary="Delete a training group",
        description="**Who can delete:** Admin or Club users only.",
    ),
    members=extend_schema(
        tags=["Tennis - Groups"],
        summary="List active members of a group",
        description="Returns all active `GroupMembership` records for this group.",
    ),
    notes=extend_schema(
        tags=["Tennis - Groups"],
        summary="List / add notes for a group",
        description=(
            "**GET** → returns all notes for this group (Admin or Coach).\n\n"
            "**POST** → adds a note. Supply `player` UUID to attach to a specific player, "
            "or leave blank for a general group note.\n\n"
            "**Who can access:** Admin or Coach."
        ),
    ),
    close=extend_schema(
        tags=["Tennis - Groups"],
        summary="Close a group",
        description=(
            "Sets group status to `closed`. Closed groups cannot have new sessions.\n\n"
            "**Who can close:** Admin, the assigned Coach, or the linked Club."
        ),
    ),
    add_player=extend_schema(
        tags=["Tennis - Groups"],
        summary="Add a player to a group",
        description=(
            "Two modes — supply **exactly one** of the following:\n\n"
            "**Case A — existing player profile:**\n"
            '```json\n{ "player": "<player-profile-uuid>" }\n```\n'
            "Creates or reactivates a `GroupMembership` for that player.\n\n"
            "**Case B — new user (create if needed):**\n"
            "```json\n"
            "{\n"
            '  "email":        "ali@example.com",\n'
            '  "first_name":   "Ali",\n'
            '  "last_name":    "Hassan",\n'
            '  "phone_number": "+966500000000"\n'
            "}\n"
            "```\n"
            "- If a user with that e-mail exists, their account is reused.\n"
            "- A `PlayerProfile` is created if they don't have one yet.\n"
            "- A `GroupMembership` is created or reactivated.\n\n"
            "**Who can use:** Admin, the assigned Coach, or the linked Club."
        ),
        request=AddPlayerToGroupSerializer,
        responses={201: GroupMembershipSerializer},
    ),
    report=extend_schema(
        tags=["Tennis - Groups"],
        summary="Group report",
        description=(
            "Returns a summary report for the group including:\n\n"
            "- Member count and list\n"
            "- Session breakdown (total / completed / scheduled)\n"
            "- Attendance summary (present / absent / late / excused)\n\n"
            "**Who can access:** Admin, the assigned Coach, or the linked Club."
        ),
    ),
)
class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.select_related("club", "coach__user", "location").order_by(
        "-created_at"
    )
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = GroupFilter

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdminOrClub()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Group.objects.none()
        qs = super().get_queryset()
        user = self.request.user
        if user.user_type == UserType.ADMIN:
            return qs
        if hasattr(user, "club_profile"):
            return qs.filter(club=user.club_profile)
        if hasattr(user, "coach_profile"):
            return qs.filter(coach=user.coach_profile)
        if hasattr(user, "player_profile"):
            member_group_ids = GroupMembership.objects.filter(
                player=user.player_profile, is_active=True
            ).values_list("group_id", flat=True)
            return qs.filter(id__in=member_group_ids)
        # Other user types: show groups they created (via BaseModel created_by)
        return qs.filter(created_by=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user

        # ── Coach: default to own profile, cannot assign another coach ─
        if hasattr(user, "coach_profile"):
            if data.get("coach") is None:
                data["coach"] = user.coach_profile
            elif (
                data["coach"] != user.coach_profile and user.user_type != UserType.ADMIN
            ):
                return Response(
                    {
                        "detail": "Coaches can only create groups assigned to themselves."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # ── Club: auto-set club, restrict coach to affiliated ones ──────
        elif hasattr(user, "club_profile"):
            if not data.get("club"):
                data["club"] = user.club_profile
            if data.get("coach") is not None:
                from tennis.models import Affiliation, AffiliationLinkType

                club = data.get("club", user.club_profile)
                if not Affiliation.objects.filter(
                    requester=data["coach"].user,
                    target=club.user,
                    link_type=AffiliationLinkType.COACH_CLUB,
                    status=AffiliationStatus.ACTIVE,
                ).exists():
                    return Response(
                        {
                            "detail": (
                                "You can only assign coaches with an active affiliation "
                                "with your club."
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

        # ── Non-admin: cannot assign someone else's coach ───────────────
        elif user.user_type != UserType.ADMIN and data.get("coach") is not None:
            return Response(
                {"detail": "Only club or admin users can assign a coach to a group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save(created_by=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        group = self.get_object()
        user = request.user
        if not self._can_manage(user, group):
            return Response(
                {"detail": "You do not have permission to update this group."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def _can_manage(self, user, group):
        if user.user_type == UserType.ADMIN:
            return True
        if hasattr(user, "coach_profile") and group.coach == user.coach_profile:
            return True
        if hasattr(user, "club_profile") and group.club == user.club_profile:
            return True
        if group.created_by == user:
            return True
        return False

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        group = self.get_object()
        memberships = group.memberships.select_related("player__user").filter(
            is_active=True
        )
        page = self.paginate_queryset(memberships)
        if page is not None:
            return self.get_paginated_response(
                GroupMembershipSerializer(page, many=True).data
            )
        return Response(GroupMembershipSerializer(memberships, many=True).data)

    @action(detail=True, methods=["get", "post"], permission_classes=[IsAdminOrCoach])
    def notes(self, request, pk=None):
        group = self.get_object()
        if request.method == "GET":
            notes = group.group_notes.select_related("author", "player__user")
            page = self.paginate_queryset(notes)
            if page is not None:
                return self.get_paginated_response(
                    GroupNoteSerializer(page, many=True).data
                )
            return Response(GroupNoteSerializer(notes, many=True).data)
        serializer = GroupNoteSerializer(
            data={**request.data, "group": group.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        group = self.get_object()
        if not self._can_manage(request.user, group):
            return Response(
                {"detail": "You do not have permission to close this group."},
                status=status.HTTP_403_FORBIDDEN,
            )
        group.status = GroupStatus.CLOSED
        group.save(update_fields=["status"])
        return Response(GroupSerializer(group).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="add-player",
        permission_classes=[IsAdminOrCoach],
    )
    def add_player(self, request, pk=None):
        group = self.get_object()
        serializer = AddPlayerToGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            if data.get("player"):
                try:
                    player_profile = PlayerProfile.objects.get(pk=data["player"])
                except PlayerProfile.DoesNotExist:
                    return Response(
                        {"detail": "Player profile not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                email = data["email"].lower()
                user, _ = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": data.get("first_name", ""),
                        "last_name": data.get("last_name", ""),
                        "phone_number": data.get("phone_number", ""),
                        "user_type": UserType.PLAYER,
                    },
                )
                player_profile, _ = PlayerProfile.objects.get_or_create(user=user)

            membership, created = GroupMembership.objects.get_or_create(
                group=group,
                player=player_profile,
                defaults={"is_active": True},
            )
            if not created and not membership.is_active:
                membership.is_active = True
                membership.save(update_fields=["is_active"])

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            GroupMembershipSerializer(membership).data, status=response_status
        )

    @action(detail=True, methods=["get"])
    def report(self, request, pk=None):
        group = self.get_object()
        if not self._can_manage(request.user, group):
            return Response(
                {"detail": "You do not have permission to view this report."},
                status=status.HTTP_403_FORBIDDEN,
            )

        members = group.memberships.filter(is_active=True).select_related(
            "player__user"
        )
        sessions = group.sessions.all()
        total_sessions = sessions.count()
        completed = sessions.filter(status="completed").count()
        scheduled = sessions.filter(status="scheduled").count()

        att_qs = SessionAttendance.objects.filter(session__group=group)
        att_summary = {
            "total_records": att_qs.count(),
            "present": att_qs.filter(status=AttendanceStatus.PRESENT).count(),
            "absent": att_qs.filter(status=AttendanceStatus.ABSENT).count(),
            "late": att_qs.filter(status=AttendanceStatus.LATE).count(),
            "excused": att_qs.filter(status=AttendanceStatus.EXCUSED).count(),
        }

        members_data = [
            {
                "id": str(m.player.id),
                "name": m.player.user.get_full_name(),
                "email": m.player.user.email,
            }
            for m in members
        ]

        return Response(
            {
                "group": GroupSerializer(group).data,
                "member_count": len(members_data),
                "members": members_data,
                "session_summary": {
                    "total": total_sessions,
                    "completed": completed,
                    "scheduled": scheduled,
                    "other": total_sessions - completed - scheduled,
                },
                "attendance_summary": att_summary,
            }
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Tennis - Groups"],
        summary="List group memberships",
        description=(
            "Each record represents a player enrolled in a group.\n\n"
            "**Filters:** `?group=<uuid>`, `?player=<uuid>`, `?is_active=true|false`"
        ),
    ),
    retrieve=extend_schema(tags=["Tennis - Groups"], summary="Get a group membership"),
    create=extend_schema(
        tags=["Tennis - Groups"],
        summary="Add a player to a group",
        description="**Who can add:** Admin or Coach users only.",
    ),
    update=extend_schema(tags=["Tennis - Groups"], summary="Update group membership"),
    partial_update=extend_schema(
        tags=["Tennis - Groups"], summary="Partially update group membership"
    ),
    destroy=extend_schema(
        tags=["Tennis - Groups"],
        summary="Remove a player from a group",
        description="**Who can remove:** Admin or Coach users only.",
    ),
)
class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.select_related("group", "player__user").order_by(
        "-created_at"
    )
    serializer_class = GroupMembershipSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = GroupMembershipFilter

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsAdminOrCoach()]
        return [IsAuthenticated()]


@extend_schema_view(
    list=extend_schema(
        tags=["Tennis - Groups"],
        summary="List group notes",
        description=(
            "Coaching notes written about groups or individual players in a group.\n\n"
            "**Filters:** `?group=<uuid>`, `?player=<uuid>`\n\n"
            "**Who can access:** Admin or Coach only."
        ),
    ),
    retrieve=extend_schema(tags=["Tennis - Groups"], summary="Get a group note"),
    create=extend_schema(
        tags=["Tennis - Groups"],
        summary="Create a group note",
        description=(
            "Write a coaching note. Supply `player` to attach to a specific player, "
            "or omit for a general group note.\n\n"
            "**Who can create:** Admin or Coach only. Author is set automatically."
        ),
    ),
    update=extend_schema(tags=["Tennis - Groups"], summary="Update a group note"),
    partial_update=extend_schema(
        tags=["Tennis - Groups"], summary="Partially update a group note"
    ),
    destroy=extend_schema(tags=["Tennis - Groups"], summary="Delete a group note"),
)
class GroupNoteViewSet(viewsets.ModelViewSet):
    queryset = GroupNote.objects.select_related(
        "group", "player__user", "author"
    ).order_by("-created_at")
    serializer_class = GroupNoteSerializer
    permission_classes = [IsAdminOrCoach]
    filter_backends = [DjangoFilterBackend]
    filterset_class = GroupNoteFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@extend_schema(
    tags=["Tennis - Groups"],
    summary="Search users / players",
    description=(
        "Search for users by **name**, **e-mail**, or **phone number**.\n\n"
        "Use this before calling `POST /groups/{id}/add-player/` to find the right person.\n\n"
        "**Query parameter:** `?q=<search term>` (min 2 characters)\n\n"
        "**Who can search:** Admin or Coach only."
    ),
    parameters=[
        OpenApiParameter(
            name="q",
            description="Search term — matches name, e-mail, or phone number.",
            required=True,
            type=str,
        )
    ],
    responses={200: PlayerSearchResultSerializer(many=True)},
)
class PlayerSearchView(APIView):
    permission_classes = [IsAdminOrCoach]

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if len(q) < 2:
            return Response(
                {"detail": "Search term must be at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        users = (
            User.objects.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(phone_number__icontains=q)
            )
            .prefetch_related("player_profile")
            .order_by("first_name", "last_name")[:50]
        )

        results = []
        for user in users:
            profile = getattr(user, "player_profile", None)
            results.append(
                {
                    "user_id": user.id,
                    "full_name": user.get_full_name(),
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "user_type": user.user_type,
                    "has_player_profile": profile is not None,
                    "player_profile_id": profile.id if profile else None,
                }
            )

        return Response(PlayerSearchResultSerializer(results, many=True).data)


@extend_schema(
    tags=["Tennis - Sessions"],
    summary="My session calendar",
    description=(
        "Returns sessions relevant to the requesting user, ordered by date and time.\n\n"
        "**Who sees what:**\n"
        "- **Coach** → sessions they are assigned to coach\n"
        "- **Player** → sessions from groups they are an active member of\n"
        "- **Everyone** → sessions where they appear in attendance records\n\n"
        "**Date filters (optional):**\n"
        "- `?date=YYYY-MM-DD` — exact date (overrides range)\n"
        "- `?date_from=YYYY-MM-DD` — start of range\n"
        "- `?date_to=YYYY-MM-DD` — end of range\n\n"
        "Omit all filters to return all upcoming and past sessions."
    ),
    parameters=[
        OpenApiParameter("date", description="Exact date (YYYY-MM-DD)", type=str),
        OpenApiParameter("date_from", description="Range start (YYYY-MM-DD)", type=str),
        OpenApiParameter("date_to", description="Range end (YYYY-MM-DD)", type=str),
    ],
)
class CalendarView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SessionSerializer

    def get(self, request):
        user = request.user
        conditions = Q(pk__isnull=True)  # start empty

        if hasattr(user, "coach_profile"):
            conditions |= Q(coach=user.coach_profile)

        if hasattr(user, "player_profile"):
            group_ids = GroupMembership.objects.filter(
                player=user.player_profile, is_active=True
            ).values_list("group_id", flat=True)
            conditions |= Q(group_id__in=group_ids)

        conditions |= Q(attendances__player=user)

        qs = (
            Session.objects.filter(conditions)
            .distinct()
            .select_related("group", "coach__user", "location")
            .prefetch_related("attendances")
        )

        date = request.query_params.get("date")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if date:
            qs = qs.filter(date=date)
        else:
            if date_from:
                qs = qs.filter(date__gte=date_from)
            if date_to:
                qs = qs.filter(date__lte=date_to)

        qs = qs.order_by("date", "start_time")

        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                SessionSerializer(page, many=True, context={"request": request}).data
            )
        return Response(
            SessionSerializer(qs, many=True, context={"request": request}).data
        )

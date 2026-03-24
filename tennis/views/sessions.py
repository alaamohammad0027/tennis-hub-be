from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from tennis.filters import SessionFilter, SessionAttendanceFilter, SessionNoteFilter
from tennis.models import Session, SessionAttendance, SessionNote, SessionStatus
from tennis.serializers import (
    SessionSerializer,
    SessionAttendanceSerializer,
    SessionNoteSerializer,
    SessionCloneSerializer,
)
from tennis.permissions import IsAdmin, IsAdminOrCoach


@extend_schema_view(
    list=extend_schema(
        tags=["Tennis - Sessions"],
        summary="List sessions",
        description=(
            "Returns training sessions.\n\n"
            "**Filters:**\n"
            "- `?group=<uuid>` — sessions for a specific group\n"
            "- `?coach=<uuid>` — sessions by a specific coach\n"
            "- `?status=scheduled|active|completed|terminated`\n"
            "- `?date=YYYY-MM-DD` — exact date\n"
            "- `?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` — date range\n"
            "- `?payment_status=pending|paid|waived`"
        ),
    ),
    retrieve=extend_schema(tags=["Tennis - Sessions"], summary="Get a session"),
    create=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Create a session",
        description="**Who can create:** Admin or Coach users only.",
    ),
    update=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Update a session",
        description="**Who can update:** Admin or Coach users only.",
    ),
    partial_update=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Partially update a session",
        description="**Who can update:** Admin or Coach users only.",
    ),
    destroy=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Delete a session",
        description="**Who can delete:** Admin or Coach users only.",
    ),
    terminate=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Terminate a session",
        description=(
            "Sets the session status to `terminated`. "
            "Use this instead of deleting when a session is cancelled mid-way.\n\n"
            "**Who can terminate:** Admin or Coach."
        ),
    ),
    clone=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Clone (repeat) a session",
        description=(
            "Creates a new session based on this one — useful for recurring sessions. "
            "Supply a new `date` and optionally override `start_time`, `end_time`, `title`.\n\n"
            "**Who can clone:** Admin or Coach."
        ),
        request=SessionCloneSerializer,
    ),
    attendance=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Get attendance for a session",
        description="Returns all attendance records for this session. Available to all authenticated users.",
    ),
    notes=extend_schema(
        tags=["Tennis - Sessions"],
        summary="List / add notes for a session",
        description=(
            "**GET** → returns all coaching notes for this session.\n\n"
            "**POST** → adds a new note. Author is set automatically.\n\n"
            "**Who can access:** Admin or Coach only."
        ),
    ),
    by_link=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Get session by deep link",
        description=(
            "Public endpoint — no authentication required. "
            "Each session has a unique `deep_link` code (e.g. from a QR code or shared URL). "
            "Returns a compact view with title, date, time, group, coach and location."
        ),
    ),
)
class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.select_related(
        "group", "coach__user", "location"
    ).order_by("-date", "-start_time")
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SessionFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Session.objects.none()
        return super().get_queryset()

    def get_permissions(self):
        if self.action == "by_link":
            return [AllowAny()]
        if self.action in (
            "create",
            "destroy",
            "update",
            "partial_update",
            "terminate",
        ):
            return [IsAdminOrCoach()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrCoach])
    def terminate(self, request, pk=None):
        session = self.get_object()
        if session.status == SessionStatus.TERMINATED:
            return Response(
                {"detail": "Session is already terminated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session.status = SessionStatus.TERMINATED
        session.save(update_fields=["status"])
        return Response(SessionSerializer(session).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrCoach])
    def clone(self, request, pk=None):
        session = self.get_object()
        serializer = SessionCloneSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        clone = serializer.create_clone(session, serializer.validated_data)
        return Response(SessionSerializer(clone).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def attendance(self, request, pk=None):
        session = self.get_object()
        attendances = session.attendances.select_related("player")
        page = self.paginate_queryset(attendances)
        if page is not None:
            return self.get_paginated_response(
                SessionAttendanceSerializer(page, many=True).data
            )
        return Response(SessionAttendanceSerializer(attendances, many=True).data)

    @action(detail=True, methods=["get", "post"], permission_classes=[IsAdminOrCoach])
    def notes(self, request, pk=None):
        session = self.get_object()
        if request.method == "GET":
            notes = session.session_notes.select_related("author")
            page = self.paginate_queryset(notes)
            if page is not None:
                return self.get_paginated_response(
                    SessionNoteSerializer(page, many=True).data
                )
            return Response(SessionNoteSerializer(notes, many=True).data)
        serializer = SessionNoteSerializer(
            data={**request.data, "session": session.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="by-link/(?P<deep_link>[^/.]+)")
    def by_link(self, request, deep_link=None):
        session = Session.objects.filter(deep_link=deep_link).first()
        if not session:
            return Response(
                {"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            SessionSerializer(
                session,
                fields=[
                    "id",
                    "title",
                    "date",
                    "start_time",
                    "end_time",
                    "group_name",
                    "coach_name",
                    "location_name",
                    "status",
                ],
            ).data
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Tennis - Sessions"],
        summary="List attendance records",
        description=(
            "Each record represents one player's attendance for one session.\n\n"
            "**Filters:** `?session=<uuid>`, `?player=<uuid>`, "
            "`?status=present|absent|late|excused`\n\n"
            "**Who can access:** Admin or Coach only."
        ),
    ),
    retrieve=extend_schema(
        tags=["Tennis - Sessions"], summary="Get an attendance record"
    ),
    create=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Mark attendance",
        description=(
            "Record a player's attendance for a session.\n\n"
            "**Who can mark:** Admin or Coach only."
        ),
    ),
    update=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Update attendance status",
        description="**Who can update:** Admin or Coach only.",
    ),
    partial_update=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Partially update attendance",
        description="**Who can update:** Admin or Coach only.",
    ),
    destroy=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Delete an attendance record",
        description="**Who can delete:** Admin or Coach only.",
    ),
)
class SessionAttendanceViewSet(viewsets.ModelViewSet):
    queryset = SessionAttendance.objects.select_related("session", "player").order_by(
        "-created_at"
    )
    serializer_class = SessionAttendanceSerializer
    permission_classes = [IsAdminOrCoach]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SessionAttendanceFilter


@extend_schema_view(
    list=extend_schema(
        tags=["Tennis - Sessions"],
        summary="List session notes",
        description=(
            "Coaching notes written about a session.\n\n"
            "**Filters:** `?session=<uuid>`\n\n"
            "**Who can access:** Admin or Coach only."
        ),
    ),
    retrieve=extend_schema(tags=["Tennis - Sessions"], summary="Get a session note"),
    create=extend_schema(
        tags=["Tennis - Sessions"],
        summary="Create a session note",
        description=(
            "Write a note about a session. Author is set automatically.\n\n"
            "**Who can create:** Admin or Coach only."
        ),
    ),
    update=extend_schema(tags=["Tennis - Sessions"], summary="Update a session note"),
    partial_update=extend_schema(
        tags=["Tennis - Sessions"], summary="Partially update a session note"
    ),
    destroy=extend_schema(tags=["Tennis - Sessions"], summary="Delete a session note"),
)
class SessionNoteViewSet(viewsets.ModelViewSet):
    queryset = SessionNote.objects.select_related("session", "author").order_by(
        "-created_at"
    )
    serializer_class = SessionNoteSerializer
    permission_classes = [IsAdminOrCoach]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SessionNoteFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

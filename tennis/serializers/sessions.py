from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from core.services.serializers import DynamicFieldsModelSerializer
from tennis.models import Session, SessionAttendance, SessionNote


class SessionSerializer(DynamicFieldsModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    coach_name = serializers.CharField(
        source="coach.user.get_full_name", read_only=True, default=None
    )
    location_name = serializers.CharField(
        source="location.name", read_only=True, default=None
    )
    attendance_count = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            "id",
            "group",
            "group_name",
            "coach",
            "coach_name",
            "location",
            "location_name",
            "location_manual",
            "title",
            "date",
            "start_time",
            "end_time",
            "deadline",
            "status",
            "plan",
            "summary",
            "notes",
            "deep_link",
            "payment_status",
            "is_repeat",
            "repeated_from",
            "attendance_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "group_name",
            "coach_name",
            "location_name",
            "deep_link",
            "is_repeat",
            "repeated_from",
            "attendance_count",
            "created_at",
            "updated_at",
        ]

    def get_attendance_count(self, obj):
        return obj.attendances.count()

    def validate(self, attrs):
        # ── Max sessions cap ─────────────────────────────────────────────
        group = attrs.get("group") or (self.instance and self.instance.group)
        if group and group.max_sessions is not None and not self.instance:
            current_count = Session.objects.filter(group=group).count()
            if current_count >= group.max_sessions:
                raise serializers.ValidationError(
                    {
                        "group": (
                            f"This group has reached its session limit "
                            f"({group.max_sessions} sessions)."
                        )
                    }
                )

        # ── Coach time conflict ───────────────────────────────────────────
        coach = attrs.get("coach") or (self.instance and self.instance.coach)
        date = attrs.get("date") or (self.instance and self.instance.date)
        start_time = attrs.get("start_time") or (
            self.instance and self.instance.start_time
        )
        end_time = attrs.get("end_time") or (self.instance and self.instance.end_time)

        if coach and date and start_time and end_time:
            conflict_qs = Session.objects.filter(
                coach=coach,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
            if self.instance:
                conflict_qs = conflict_qs.exclude(pk=self.instance.pk)
            conflict = conflict_qs.select_related("group").first()
            if conflict:
                raise serializers.ValidationError(
                    {
                        "coach": (
                            f"This coach already has a session '{conflict.title}' "
                            f"in group '{conflict.group.name}' on {date} "
                            f"from {conflict.start_time} to {conflict.end_time}."
                        )
                    }
                )
        return attrs


class SessionCloneSerializer(serializers.Serializer):
    """Input serializer for cloning/repeating a session."""

    date = serializers.DateField(required=True)
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
    title = serializers.CharField(max_length=200, required=False)

    def create_clone(self, original_session, validated_data):
        clone = Session.objects.create(
            group=original_session.group,
            coach=original_session.coach,
            location=original_session.location,
            title=validated_data.get("title", original_session.title),
            date=validated_data["date"],
            start_time=validated_data.get("start_time", original_session.start_time),
            end_time=validated_data.get("end_time", original_session.end_time),
            deadline=original_session.deadline,
            notes=original_session.notes,
            payment_status=original_session.payment_status,
            is_repeat=True,
            repeated_from=original_session,
            created_by=self.context.get("request")
            and self.context["request"].user
            or None,
        )
        return clone


class SessionAttendanceSerializer(DynamicFieldsModelSerializer):
    player_full_name = serializers.CharField(
        source="player.get_full_name", read_only=True
    )
    player_email = serializers.EmailField(source="player.email", read_only=True)
    session_title = serializers.CharField(source="session.title", read_only=True)

    class Meta:
        model = SessionAttendance
        fields = [
            "id",
            "session",
            "session_title",
            "player",
            "player_full_name",
            "player_email",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "player_full_name",
            "player_email",
            "session_title",
            "created_at",
            "updated_at",
        ]


class SessionNoteSerializer(DynamicFieldsModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    session_title = serializers.CharField(source="session.title", read_only=True)

    class Meta:
        model = SessionNote
        fields = [
            "id",
            "session",
            "session_title",
            "author",
            "author_name",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "author_name",
            "session_title",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["author"] = request.user
        return super().create(validated_data)

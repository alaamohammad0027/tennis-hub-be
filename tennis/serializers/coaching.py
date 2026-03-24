from rest_framework import serializers
from core.services.serializers import DynamicFieldsModelSerializer
from tennis.models import TrainingLocation, Group, GroupMembership, GroupNote


class PlayerSearchResultSerializer(serializers.Serializer):
    """Read-only: one row returned by the player-search endpoint."""

    user_id = serializers.UUIDField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    user_type = serializers.CharField()
    has_player_profile = serializers.BooleanField()
    player_profile_id = serializers.UUIDField(allow_null=True)


class AddPlayerToGroupSerializer(serializers.Serializer):
    """
    Input for `POST /groups/{id}/add-player/`.

    **Two mutually exclusive modes:**

    **Case A — existing player profile:**
    ```json
    { "player": "<player-profile-uuid>" }
    ```
    The player must already have a `PlayerProfile`. A `GroupMembership` is
    created (or reactivated if it previously existed).

    **Case B — create new user + profile:**
    ```json
    {
      "email":        "ali@example.com",
      "first_name":   "Ali",
      "last_name":    "Hassan",
      "phone_number": "+966500000000"   // optional
    }
    ```
    - If a user with that e-mail already exists their account is reused.
    - A `PlayerProfile` is created for them if they don't have one yet.
    - A `GroupMembership` is created (or reactivated).

    Exactly one of `player` **or** `email` must be supplied.
    """

    # Case A
    player = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="UUID of an existing PlayerProfile.",
    )

    # Case B
    email = serializers.EmailField(
        required=False,
        allow_null=True,
        help_text="E-mail of the user to add (creates user+profile if needed).",
    )
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Required when creating a new user.",
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Required when creating a new user.",
    )
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional phone number when creating a new user.",
    )

    def validate(self, attrs):
        has_player = bool(attrs.get("player"))
        has_email = bool(attrs.get("email"))
        if has_player and has_email:
            raise serializers.ValidationError(
                "Provide either 'player' or 'email', not both."
            )
        if not has_player and not has_email:
            raise serializers.ValidationError(
                "Provide either 'player' (existing profile UUID) or 'email' (new user)."
            )
        return attrs


class TrainingLocationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TrainingLocation
        fields = [
            "id",
            "name",
            "address",
            "court_type",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GroupSerializer(DynamicFieldsModelSerializer):
    club_name = serializers.CharField(
        source="club.club_name", read_only=True, default=None
    )
    coach_name = serializers.CharField(
        source="coach.user.get_full_name", read_only=True, default=None
    )
    location_name = serializers.CharField(
        source="location.name", read_only=True, default=None
    )
    current_enrollment = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "club",
            "club_name",
            "coach",
            "coach_name",
            "location",
            "location_name",
            "location_manual",
            "schedule",
            "max_capacity",
            "max_sessions",
            "current_enrollment",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "club_name",
            "coach_name",
            "location_name",
            "current_enrollment",
            "created_at",
            "updated_at",
        ]


class GroupMembershipSerializer(DynamicFieldsModelSerializer):
    player_name = serializers.CharField(
        source="player.user.get_full_name", read_only=True
    )
    player_email = serializers.EmailField(source="player.user.email", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = GroupMembership
        fields = [
            "id",
            "group",
            "group_name",
            "player",
            "player_name",
            "player_email",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "player_name",
            "player_email",
            "group_name",
            "created_at",
            "updated_at",
        ]


class GroupNoteSerializer(DynamicFieldsModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    player_name = serializers.CharField(
        source="player.user.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = GroupNote
        fields = [
            "id",
            "group",
            "player",
            "player_name",
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
            "player_name",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)

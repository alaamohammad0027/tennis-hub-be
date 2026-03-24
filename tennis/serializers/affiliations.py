from rest_framework import serializers

from tennis.models import Affiliation, AffiliationLinkType, derive_link_type


class AffiliationSerializer(serializers.ModelSerializer):
    """
    Unified affiliation serializer.

    On **create** the client only supplies:
      - `target`   — UUID of the user they are requesting to join (club or federation user)
      - `role`     — optional coach role (head_coach / assistant_coach / guest_coach)
      - `location` — optional training location UUID (mainly for coach affiliations)
      - `document` — optional file attachment
      - `notes`    — optional free text
      - `joined_at`— optional date

    `requester`, `link_type`, and `status` are set automatically by the server.
    """

    requester_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Affiliation
        fields = [
            "id",
            "requester",
            "requester_name",
            "target",
            "target_name",
            "link_type",
            "status",
            "role",
            "location",
            "document",
            "notes",
            "joined_at",
            "verified_by",
            "verified_by_name",
            "verified_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "requester",
            "requester_name",
            "target_name",
            "link_type",
            "status",
            "verified_by",
            "verified_by_name",
            "verified_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "target": {
                "help_text": (
                    "UUID of the user you are requesting to join. "
                    "Must be a club user (for coach/player/referee) "
                    "or federation user (for club/referee). "
                    "The `link_type` is derived automatically from your user type and the target's type."
                )
            },
            "role": {
                "help_text": (
                    "Coach role at the club. Only relevant for coach affiliations. "
                    "Choices: `head_coach`, `assistant_coach`, `guest_coach`."
                )
            },
            "document": {
                "help_text": "Optional supporting document (contract, license scan, etc.)."
            },
        }

    def get_requester_name(self, obj):
        return obj.requester.get_full_name()

    def get_target_name(self, obj):
        return obj.target.get_full_name()

    def get_verified_by_name(self, obj):
        return obj.verified_by.get_full_name() if obj.verified_by else None

    def validate(self, attrs):
        request = self.context["request"]
        requester = request.user
        target = attrs.get("target")

        if target and target == requester:
            raise serializers.ValidationError(
                {"target": "You cannot create an affiliation with yourself."}
            )

        if target:
            link_type = derive_link_type(requester.user_type, target.user_type)
            if link_type is None:
                raise serializers.ValidationError(
                    {
                        "target": (
                            f"No valid affiliation between a '{requester.user_type}' "
                            f"and a '{target.user_type}'."
                        )
                    }
                )
            attrs["link_type"] = link_type

        return attrs

    def create(self, validated_data):
        validated_data["requester"] = self.context["request"].user
        return super().create(validated_data)

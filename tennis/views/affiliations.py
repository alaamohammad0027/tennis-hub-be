from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models.profiles.base import VerificationStatus
from accounts.models.choices import UserType
from tennis.filters import AffiliationFilter
from tennis.models import Affiliation, AffiliationStatus
from tennis.serializers import AffiliationSerializer

_RESETTABLE = {AffiliationStatus.SUSPENDED, AffiliationStatus.LEFT}


def _target_is_approved(target_user):
    """Return True if the target user's profile is APPROVED."""
    for attr in (
        "federation_profile",
        "club_profile",
        "coach_profile",
        "referee_profile",
        "player_profile",
        "fan_profile",
    ):
        profile = getattr(target_user, attr, None)
        if profile is not None:
            return (
                getattr(profile, "verification_status", None)
                == VerificationStatus.APPROVED
            )
    return False


@extend_schema_view(
    list=extend_schema(
        tags=["Tennis - Affiliations"],
        summary="List affiliations",
        description=(
            "Returns affiliations visible to the authenticated user.\n\n"
            "**Who sees what:**\n"
            "- **Club / Federation** → affiliations where they are the `target` (incoming requests) "
            "plus their own outgoing requests\n"
            "- **Coach / Player / Referee** → their own affiliations (outgoing)\n"
            "- **Admin** → all affiliations\n\n"
            "**Filters:** `?status=`, `?link_type=`, `?target=<uuid>`, `?requester=<uuid>`"
        ),
    ),
    retrieve=extend_schema(
        tags=["Tennis - Affiliations"], summary="Get affiliation detail"
    ),
    create=extend_schema(
        tags=["Tennis - Affiliations"],
        summary="Request an affiliation",
        description=(
            "Creates a new affiliation request. The `requester` is set automatically to the "
            "authenticated user. The `link_type` is derived from user types:\n\n"
            "| Requester type | Target type | link_type |\n"
            "|---|---|---|\n"
            "| `club` | `federation` | `club_federation` |\n"
            "| `coach` | `club` | `coach_club` |\n"
            "| `player` | `club` | `player_club` |\n"
            "| `referee` | `club` | `referee_club` |\n"
            "| `referee` | `federation` | `referee_federation` |\n\n"
            "If a previous request was `suspended` or `left`, re-submitting resets it to `pending`."
        ),
    ),
    update=extend_schema(
        tags=["Tennis - Affiliations"],
        summary="Update affiliation",
        description="Update mutable fields (`role`, `location`, `document`, `notes`, `joined_at`).",
    ),
    partial_update=extend_schema(
        tags=["Tennis - Affiliations"], summary="Partially update affiliation"
    ),
    destroy=extend_schema(
        tags=["Tennis - Affiliations"],
        summary="Delete / leave affiliation",
    ),
    approve=extend_schema(
        tags=["Tennis - Affiliations"],
        summary="Approve affiliation",
        description=(
            "Approve the request. **The target user (club / federation) or Admin** can approve.\n\n"
            "The target's profile must be `approved` — unverified clubs/federations "
            "cannot approve incoming requests."
        ),
    ),
    reject=extend_schema(
        tags=["Tennis - Affiliations"],
        summary="Reject affiliation",
        description=(
            "Reject the request. **The target user (club / federation) or Admin** can reject.\n\n"
            "The target's profile must be `approved`.\n\n"
            'Body: `{"reason": "<why rejected>"}`'
        ),
    ),
)
class AffiliationViewSet(viewsets.ModelViewSet):
    queryset = Affiliation.objects.select_related(
        "requester", "target", "location", "verified_by"
    ).order_by("-created_at")
    serializer_class = AffiliationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AffiliationFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Affiliation.objects.none()

        user = self.request.user
        if user.user_type == UserType.ADMIN:
            return super().get_queryset()

        # Club / Federation: see incoming requests + own outgoing
        if user.user_type in (UserType.CLUB, UserType.FEDERATION):
            return super().get_queryset().filter(Q(target=user) | Q(requester=user))

        # Others: own affiliations only
        return super().get_queryset().filter(requester=user)

    def create(self, request, *args, **kwargs):
        if request.user.user_type not in ("club", "coach", "player", "referee"):
            return Response(
                {"detail": "Your user type cannot create affiliation requests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target = serializer.validated_data["target"]
        link_type = serializer.validated_data["link_type"]

        existing = Affiliation.objects.filter(
            requester=request.user, target=target, link_type=link_type
        ).first()
        if existing:
            if existing.status in _RESETTABLE:
                existing.status = AffiliationStatus.PENDING
                existing.rejection_reason = ""
                existing.verified_by = None
                existing.verified_at = None
                existing.save(
                    update_fields=[
                        "status",
                        "rejection_reason",
                        "verified_by",
                        "verified_at",
                    ]
                )
                return Response(
                    self.get_serializer(existing).data, status=status.HTTP_200_OK
                )
            return Response(
                {
                    "detail": "An active or pending affiliation with this target already exists."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        if not self._can_verify(request, obj):
            return Response(
                {"detail": "Not authorized to approve this affiliation."},
                status=status.HTTP_403_FORBIDDEN,
            )
        obj.approve(by_user=request.user)
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        obj = self.get_object()
        if not self._can_verify(request, obj):
            return Response(
                {"detail": "Not authorized to reject this affiliation."},
                status=status.HTTP_403_FORBIDDEN,
            )
        reason = request.data.get("reason", "")
        obj.reject(by_user=request.user, reason=reason)
        return Response(self.get_serializer(obj).data)

    def _can_verify(self, request, obj):
        """Admin can always verify. Otherwise only the target user can verify,
        and the target's profile must be APPROVED."""
        if request.user.user_type == UserType.ADMIN:
            return True
        if request.user == obj.target:
            return _target_is_approved(obj.target)
        return False

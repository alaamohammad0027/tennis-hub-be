from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel


class AffiliationStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    ACTIVE = "active", _("Active")
    SUSPENDED = "suspended", _("Suspended")
    LEFT = "left", _("Left / Ended")


class AffiliationLinkType(models.TextChoices):
    CLUB_FEDERATION = "club_federation", _("Club → Federation")
    COACH_CLUB = "coach_club", _("Coach → Club")
    PLAYER_CLUB = "player_club", _("Player → Club")
    REFEREE_CLUB = "referee_club", _("Referee → Club")
    REFEREE_FEDERATION = "referee_federation", _("Referee → Federation")


class CoachRole(models.TextChoices):
    HEAD_COACH = "head_coach", _("Head Coach")
    ASSISTANT_COACH = "assistant_coach", _("Assistant Coach")
    GUEST_COACH = "guest_coach", _("Guest / Part-time Coach")


# Maps (requester user_type, target user_type) → link_type
_LINK_TYPE_MAP = {
    ("club", "federation"): AffiliationLinkType.CLUB_FEDERATION,
    ("coach", "club"): AffiliationLinkType.COACH_CLUB,
    ("player", "club"): AffiliationLinkType.PLAYER_CLUB,
    ("referee", "club"): AffiliationLinkType.REFEREE_CLUB,
    ("referee", "federation"): AffiliationLinkType.REFEREE_FEDERATION,
}

VALID_REQUESTER_TYPES = {"club", "coach", "player", "referee"}
VALID_TARGET_TYPES = {"club", "federation"}


def derive_link_type(requester_user_type, target_user_type):
    """Return the AffiliationLinkType for the given pair, or None if invalid."""
    return _LINK_TYPE_MAP.get((requester_user_type, target_user_type))


class Affiliation(BaseModel):
    """
    Single unified affiliation/link record between any two user types.

    Replaces: ClubFederationLink, CoachClubAffiliation, PlayerClubMembership, RefereeAffiliation.

    The `link_type` is derived automatically from requester + target user types:
      - Club → Federation:  club_federation
      - Coach → Club:       coach_club
      - Player → Club:      player_club
      - Referee → Club:     referee_club
      - Referee → Federation: referee_federation

    `requester` is always auto-set from `request.user` (never provided by the client).
    `status` starts as PENDING and is managed via approve/reject actions.
    """

    requester = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="affiliations_sent",
        verbose_name=_("Requester"),
    )
    target = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="affiliations_received",
        verbose_name=_("Target"),
    )
    link_type = models.CharField(
        _("Link Type"),
        max_length=30,
        choices=AffiliationLinkType.choices,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AffiliationStatus.choices,
        default=AffiliationStatus.PENDING,
    )
    # Coach-specific
    role = models.CharField(
        _("Role"),
        max_length=30,
        choices=CoachRole.choices,
        blank=True,
        default="",
        help_text=_("Only relevant for coach affiliations."),
    )
    location = models.ForeignKey(
        "tennis.TrainingLocation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="affiliations",
        verbose_name=_("Location"),
        help_text=_("Optional training location, mainly for coach affiliations."),
    )
    # General
    document = models.FileField(
        _("Supporting Document"),
        upload_to="affiliations/docs/",
        null=True,
        blank=True,
        help_text=_("Optional file attachment (contract, license scan, etc.)."),
    )
    notes = models.TextField(_("Notes"), blank=True)
    joined_at = models.DateField(_("Joined At"), null=True, blank=True)
    # Verification
    verified_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Verified By"),
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)

    class Meta:
        verbose_name = _("Affiliation")
        verbose_name_plural = _("Affiliations")
        unique_together = [("requester", "target", "link_type")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.requester} → {self.target} [{self.link_type}] [{self.status}]"

    def approve(self, by_user):
        self.status = AffiliationStatus.ACTIVE
        self.verified_by = by_user
        self.verified_at = timezone.now()
        self.rejection_reason = ""
        self.save(
            update_fields=["status", "verified_by", "verified_at", "rejection_reason"]
        )

    def reject(self, by_user, reason=""):
        self.status = AffiliationStatus.SUSPENDED
        self.verified_by = by_user
        self.verified_at = timezone.now()
        self.rejection_reason = reason
        self.save(
            update_fields=["status", "verified_by", "verified_at", "rejection_reason"]
        )

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel


class VerificationStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    UNDER_REVIEW = "under_review", _("Under Review")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")


class BaseProfile(BaseModel):
    """
    Abstract base for all typed profiles.

    Verification fields track WHO approved and WHEN.
    The `verified_by` user can be:
      - A platform admin (user_type=ADMIN)
      - A federation user (has FederationProfile) — can verify clubs
      - A club user (has ClubProfile) — can verify coaches/players/referees
    """

    verification_status = models.CharField(
        _("Verification Status"),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    verified_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Verified By"),
    )
    verified_at = models.DateTimeField(_("Verified At"), null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        abstract = True

    def approve(self, by_user):
        self.verification_status = VerificationStatus.APPROVED
        self.verified_by = by_user
        self.verified_at = timezone.now()
        self.rejection_reason = ""
        self.save(
            update_fields=[
                "verification_status",
                "verified_by",
                "verified_at",
                "rejection_reason",
            ]
        )

    def reject(self, by_user, reason=""):
        self.verification_status = VerificationStatus.REJECTED
        self.verified_by = by_user
        self.verified_at = timezone.now()
        self.rejection_reason = reason
        self.save(
            update_fields=[
                "verification_status",
                "verified_by",
                "verified_at",
                "rejection_reason",
            ]
        )

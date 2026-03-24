from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import BaseProfile, VerificationStatus


class FanProfile(BaseProfile):
    """
    Profile for Fans / General Users.

    No verification required — auto-approved on registration.
    Can follow players, clubs, tournaments. Cannot manage sessions or groups.
    """

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="fan_profile",
    )
    favorite_club = models.ForeignKey(
        "accounts.ClubProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fans",
    )

    # Always auto-approved — no admin review needed
    verification_status = models.CharField(
        _("Verification Status"),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.APPROVED,
        editable=False,
    )

    class Meta:
        verbose_name = _("Fan Profile")
        verbose_name_plural = _("Fan Profiles")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Fan: {self.user.get_full_name()}"

from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import BaseProfile


class RefereeLevel(models.TextChoices):
    LOCAL = "local", _("Local")
    REGIONAL = "regional", _("Regional")
    NATIONAL = "national", _("National")
    INTERNATIONAL = "international", _("International / ITF")


class RefereeProfile(BaseProfile):
    """
    Profile for Referees / Umpires.

    Verified by: Platform Admin OR any Club/Federation they are affiliated with.
    Can be affiliated with: Multiple clubs or federations.
    """

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="referee_profile",
    )
    referee_level = models.CharField(
        _("Referee Level"),
        max_length=20,
        choices=RefereeLevel.choices,
        default=RefereeLevel.LOCAL,
    )
    license_number = models.CharField(_("License Number"), max_length=100, blank=True)
    certifications = models.TextField(
        _("Certifications"), blank=True, help_text=_("Comma-separated")
    )
    years_experience = models.PositiveIntegerField(_("Years of Experience"), default=0)
    itf_badge = models.CharField(_("ITF Badge / ID"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("Referee Profile")
        verbose_name_plural = _("Referee Profiles")
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Referee: {self.user.get_full_name()} ({self.get_referee_level_display()})"
        )

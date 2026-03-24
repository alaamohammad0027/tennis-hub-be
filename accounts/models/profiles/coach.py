from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import BaseProfile


class CoachingLevel(models.TextChoices):
    BEGINNER = "beginner", _("Beginner / Recreational")
    INTERMEDIATE = "intermediate", _("Intermediate")
    ADVANCED = "advanced", _("Advanced / Competitive")
    ELITE = "elite", _("Elite / Professional")


class CoachProfile(BaseProfile):
    """
    Profile for Coaches.

    Verified by: Platform Admin OR any Club they have an active affiliation with.
    Can work at: Multiple clubs simultaneously (via tennis.Affiliation (link_type=coach_club)).
    Each club affiliation has its own verification status.
    """

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="coach_profile",
    )
    specialization = models.CharField(_("Specialization"), max_length=200, blank=True)
    coaching_level = models.CharField(
        _("Coaching Level"),
        max_length=20,
        choices=CoachingLevel.choices,
        default=CoachingLevel.INTERMEDIATE,
    )
    license_number = models.CharField(_("License Number"), max_length=100, blank=True)
    certifications = models.TextField(
        _("Certifications"), blank=True, help_text=_("Comma-separated")
    )
    years_experience = models.PositiveIntegerField(_("Years of Experience"), default=0)

    class Meta:
        verbose_name = _("Coach Profile")
        verbose_name_plural = _("Coach Profiles")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Coach: {self.user.get_full_name()}"

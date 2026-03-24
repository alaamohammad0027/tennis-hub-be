from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import BaseProfile


class SkillLevel(models.TextChoices):
    BEGINNER = "beginner", _("Beginner")
    INTERMEDIATE = "intermediate", _("Intermediate")
    ADVANCED = "advanced", _("Advanced")
    PROFESSIONAL = "professional", _("Professional")


class DominantHand(models.TextChoices):
    RIGHT = "right", _("Right")
    LEFT = "left", _("Left")
    AMBIDEXTROUS = "ambidextrous", _("Ambidextrous")


class PlayerProfile(BaseProfile):
    """
    Profile for Players.

    Verified by: Platform Admin OR any Club they have an active membership with.
    Can be a member of: Multiple clubs simultaneously (via tennis.Affiliation (link_type=player_club)).
    Each membership has its own verification status.
    """

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="player_profile",
    )
    skill_level = models.CharField(
        _("Skill Level"),
        max_length=20,
        choices=SkillLevel.choices,
        default=SkillLevel.BEGINNER,
    )
    ranking = models.PositiveIntegerField(_("Ranking"), null=True, blank=True)
    dominant_hand = models.CharField(
        _("Dominant Hand"),
        max_length=20,
        choices=DominantHand.choices,
        default=DominantHand.RIGHT,
    )

    class Meta:
        verbose_name = _("Player Profile")
        verbose_name_plural = _("Player Profiles")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Player: {self.user.get_full_name()} ({self.get_skill_level_display()})"

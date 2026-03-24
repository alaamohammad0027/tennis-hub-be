from django.db import models
from django.utils.translation import gettext_lazy as _


class UserProfileType(models.TextChoices):
    """Profile types available for public registration (no admin)."""

    FEDERATION = "federation", _("Sport Federation")
    CLUB = "club", _("Club / Academy")
    COACH = "coach", _("Coach")
    REFEREE = "referee", _("Referee")
    PLAYER = "player", _("Player")
    FAN = "fan", _("Fan / General User")


class UserType(models.TextChoices):
    """All user types including platform admin."""

    ADMIN = "admin", _("Admin")
    FEDERATION = "federation", _("Sport Federation")
    CLUB = "club", _("Club / Academy")
    COACH = "coach", _("Coach")
    REFEREE = "referee", _("Referee")
    PLAYER = "player", _("Player")
    FAN = "fan", _("Fan / General User")

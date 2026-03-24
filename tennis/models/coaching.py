from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel


class TrainingLocation(BaseModel):
    name = models.CharField(_("Name"), max_length=200)
    address = models.CharField(_("Address"), max_length=255, blank=True)
    court_type = models.CharField(_("Court Type"), max_length=100, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Training Location")
        verbose_name_plural = _("Training Locations")
        ordering = ["name"]

    def __str__(self):
        return self.name


class GroupStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    CLOSED = "closed", _("Closed")
    ARCHIVED = "archived", _("Archived")


class Group(BaseModel):
    """
    A coached training group. Can belong to a Club or be a personal/private group.
    Coach and club are both optional — any authenticated user can create a group.
    """

    name = models.CharField(_("Name"), max_length=200)
    club = models.ForeignKey(
        "accounts.ClubProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
        verbose_name=_("Club"),
    )
    coach = models.ForeignKey(
        "accounts.CoachProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
        verbose_name=_("Coach"),
    )
    location = models.ForeignKey(
        TrainingLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
        verbose_name=_("Training Location"),
    )
    location_manual = models.CharField(
        _("Manual Location"),
        max_length=255,
        blank=True,
        help_text=_("Free-text location when no TrainingLocation record is needed."),
    )
    schedule = models.TextField(_("Schedule"), blank=True)
    max_capacity = models.PositiveIntegerField(_("Max Capacity"), default=20)
    max_sessions = models.PositiveIntegerField(
        _("Max Sessions"),
        null=True,
        blank=True,
        help_text=_(
            "Optional cap on total sessions for this group. Leave blank for unlimited."
        ),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=GroupStatus.choices,
        default=GroupStatus.ACTIVE,
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def current_enrollment(self):
        return self.memberships.filter(is_active=True).count()


class GroupMembership(BaseModel):
    """Player inside a coaching group."""

    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="memberships"
    )
    player = models.ForeignKey(
        "accounts.PlayerProfile",
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    notes = models.TextField(_("Notes"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Group Membership")
        verbose_name_plural = _("Group Memberships")
        unique_together = [("group", "player")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.player} in {self.group}"


class GroupNote(BaseModel):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="group_notes"
    )
    player = models.ForeignKey(
        "accounts.PlayerProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="group_notes_about",
        verbose_name=_("Player (blank = general note)"),
    )
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="authored_group_notes",
    )
    content = models.TextField(_("Content"))

    class Meta:
        verbose_name = _("Group Note")
        verbose_name_plural = _("Group Notes")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.group} by {self.author}"

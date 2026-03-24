import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel


class SessionStatus(models.TextChoices):
    SCHEDULED = "scheduled", _("Scheduled")
    ACTIVE = "active", _("Active")
    COMPLETED = "completed", _("Completed")
    TERMINATED = "terminated", _("Terminated")


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", _("Present")
    ABSENT = "absent", _("Absent")
    LATE = "late", _("Late")
    EXCUSED = "excused", _("Excused")


class PaymentStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    PAID = "paid", _("Paid")
    WAIVED = "waived", _("Waived")


class Session(BaseModel):
    group = models.ForeignKey(
        "tennis.Group",
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    coach = models.ForeignKey(
        "accounts.CoachProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )
    location = models.ForeignKey(
        "tennis.TrainingLocation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
        verbose_name=_("Training Location"),
    )
    location_manual = models.CharField(
        _("Manual Location"),
        max_length=255,
        blank=True,
        help_text=_(
            "Free-text location — used when no TrainingLocation record is needed."
        ),
    )
    title = models.CharField(_("Title"), max_length=200)
    date = models.DateField(_("Date"))
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    deadline = models.DateTimeField(
        _("Deadline"), null=True, blank=True, help_text=_("Auto-close deadline")
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.SCHEDULED,
    )
    plan = models.TextField(
        _("Session Plan"),
        blank=True,
        help_text=_("What we plan to do this session (set before)."),
    )
    summary = models.TextField(
        _("Session Summary"),
        blank=True,
        help_text=_("What was actually done (filled after session)."),
    )
    notes = models.TextField(_("Notes"), blank=True)
    deep_link = models.CharField(
        _("Deep Link"), max_length=200, blank=True, unique=True
    )
    payment_status = models.CharField(
        _("Payment Status"),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    is_repeat = models.BooleanField(_("Is Repeat"), default=False)
    repeated_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clones",
        verbose_name=_("Repeated From"),
    )

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
        ordering = ["-date", "-start_time"]

    def __str__(self):
        return f"{self.title} ({self.date})"

    def save(self, *args, **kwargs):
        if not self.deep_link:
            self.deep_link = uuid.uuid4().hex
        super().save(*args, **kwargs)


class SessionAttendance(BaseModel):
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    player = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="session_attendances",
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.ABSENT,
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Session Attendance")
        verbose_name_plural = _("Session Attendances")
        unique_together = [("session", "player")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.player} @ {self.session} — {self.status}"


class SessionNote(BaseModel):
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="session_notes",
    )
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="authored_session_notes",
    )
    content = models.TextField(_("Content"))

    class Meta:
        verbose_name = _("Session Note")
        verbose_name_plural = _("Session Notes")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.session} by {self.author}"

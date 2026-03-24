from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from tennis.models import (
    Affiliation,
    AffiliationStatus,
    AffiliationLinkType,
    TrainingLocation,
    Group,
    GroupMembership,
    GroupNote,
    Session,
    SessionAttendance,
    AttendanceStatus,
    SessionNote,
    SessionStatus,
    PaymentStatus,
)


# ─── Shared affiliation bulk actions ──────────────────────────


def _approve_affiliations(modeladmin, request, queryset):
    queryset.update(
        status=AffiliationStatus.ACTIVE,
        verified_by=request.user,
        verified_at=timezone.now(),
        rejection_reason="",
    )


_approve_affiliations.short_description = "✔ Approve selected affiliations"


def _reject_affiliations(modeladmin, request, queryset):
    queryset.update(
        status=AffiliationStatus.SUSPENDED,
        verified_by=request.user,
        verified_at=timezone.now(),
    )


_reject_affiliations.short_description = "✘ Reject (suspend) selected affiliations"


def _reset_to_pending(modeladmin, request, queryset):
    queryset.update(
        status=AffiliationStatus.PENDING,
        verified_by=None,
        verified_at=None,
        rejection_reason="",
    )


_reset_to_pending.short_description = "↩ Reset selected to Pending"


# ─── Shared affiliation admin base ────────────────────────────


class _AffiliationAdmin(admin.ModelAdmin):
    readonly_fields = ("verified_by", "verified_at", "created_at", "updated_at")
    actions = [_approve_affiliations, _reject_affiliations, _reset_to_pending]
    list_per_page = 50

    @admin.display(description="Status")
    def status_badge(self, obj):
        colours = {
            AffiliationStatus.PENDING: "#856404",
            AffiliationStatus.ACTIVE: "#155724",
            AffiliationStatus.SUSPENDED: "#721c24",
            AffiliationStatus.LEFT: "#6c757d",
        }
        colour = colours.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 7px;'
            'border-radius:3px;font-size:11px">{}</span>',
            colour,
            obj.get_status_display(),
        )


# ─── Affiliations ──────────────────────────────────────────────


@admin.register(Affiliation)
class AffiliationAdmin(_AffiliationAdmin):
    list_display = (
        "requester",
        "target",
        "link_type",
        "role",
        "status_badge",
        "verified_by",
        "joined_at",
        "created_at",
    )
    list_filter = ("link_type", "status", "role")
    search_fields = (
        "requester__email",
        "requester__first_name",
        "requester__last_name",
        "target__email",
        "target__first_name",
        "target__last_name",
    )
    raw_id_fields = ("requester", "target", "location", "verified_by")
    date_hierarchy = "created_at"
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "requester",
                    "target",
                    "link_type",
                    "role",
                    "location",
                    "joined_at",
                    "document",
                    "notes",
                )
            },
        ),
        (
            "Verification",
            {"fields": ("status", "verified_by", "verified_at", "rejection_reason")},
        ),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )


# ─── Locations ────────────────────────────────────────────────


@admin.register(TrainingLocation)
class TrainingLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "court_type", "is_active", "created_at")
    list_filter = ("court_type", "is_active")
    search_fields = ("name", "address")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "address", "court_type", "is_active")}),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )


# ─── Groups ───────────────────────────────────────────────────


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    fields = ("player", "is_active", "notes")
    raw_id_fields = ("player",)
    show_change_link = True


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "club",
        "coach",
        "status",
        "max_capacity",
        "current_enrollment",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "name",
        "club__club_name",
        "coach__user__email",
        "coach__user__first_name",
    )
    raw_id_fields = ("club", "coach", "location")
    readonly_fields = ("current_enrollment", "created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 50
    inlines = [GroupMembershipInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "status",
                    "max_capacity",
                    "max_sessions",
                    "current_enrollment",
                    "notes",
                )
            },
        ),
        (
            "Club & Coach",
            {"fields": ("club", "coach")},
        ),
        (
            "Location & Schedule",
            {"fields": ("location", "location_manual", "schedule")},
        ),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("player", "group", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("player__user__email", "player__user__first_name", "group__name")
    raw_id_fields = ("group", "player")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"


@admin.register(GroupNote)
class GroupNoteAdmin(admin.ModelAdmin):
    list_display = ("group", "player", "author", "short_content", "created_at")
    search_fields = ("group__name", "player__user__email", "author__email", "content")
    raw_id_fields = ("group", "player", "author")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    @admin.display(description="Content")
    def short_content(self, obj):
        return (obj.content[:60] + "…") if len(obj.content) > 60 else obj.content


# ─── Sessions ─────────────────────────────────────────────────


class SessionAttendanceInline(admin.TabularInline):
    model = SessionAttendance
    extra = 0
    fields = ("player", "status", "notes")
    raw_id_fields = ("player",)

    @admin.display(description="Status")
    def status_badge(self, obj):
        colours = {
            AttendanceStatus.PRESENT: "#155724",
            AttendanceStatus.ABSENT: "#721c24",
            AttendanceStatus.LATE: "#856404",
            AttendanceStatus.EXCUSED: "#0c5460",
        }
        colour = colours.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 6px;border-radius:3px;font-size:11px">{}</span>',
            colour,
            obj.get_status_display(),
        )


class SessionNoteInline(admin.TabularInline):
    model = SessionNote
    extra = 0
    fields = ("author", "content")
    raw_id_fields = ("author",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "group",
        "coach",
        "date",
        "start_time",
        "end_time",
        "status_badge",
        "payment_badge",
        "is_repeat",
    )
    list_filter = ("status", "payment_status", "is_repeat")
    search_fields = (
        "title",
        "group__name",
        "coach__user__email",
        "coach__user__first_name",
    )
    date_hierarchy = "date"
    raw_id_fields = ("group", "coach", "location", "repeated_from")
    readonly_fields = (
        "deep_link",
        "is_repeat",
        "repeated_from",
        "created_at",
        "updated_at",
    )
    list_per_page = 50
    inlines = [SessionAttendanceInline, SessionNoteInline]
    fieldsets = (
        (
            None,
            {"fields": ("title", "group", "coach", "status")},
        ),
        (
            "Schedule",
            {"fields": ("date", "start_time", "end_time", "deadline")},
        ),
        (
            "Location",
            {"fields": ("location", "location_manual")},
        ),
        (
            "Content",
            {"fields": ("plan", "summary", "notes")},
        ),
        (
            "Payment & Repeat",
            {"fields": ("payment_status", "is_repeat", "repeated_from")},
        ),
        (
            "System",
            {
                "classes": ("collapse",),
                "fields": ("deep_link", "created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colours = {
            SessionStatus.SCHEDULED: "#856404",
            SessionStatus.ACTIVE: "#155724",
            SessionStatus.COMPLETED: "#0c5460",
            SessionStatus.TERMINATED: "#721c24",
        }
        colour = colours.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 6px;border-radius:3px;font-size:11px">{}</span>',
            colour,
            obj.get_status_display(),
        )

    @admin.display(description="Payment")
    def payment_badge(self, obj):
        colours = {
            PaymentStatus.PENDING: "#856404",
            PaymentStatus.PAID: "#155724",
            PaymentStatus.WAIVED: "#6c757d",
        }
        colour = colours.get(obj.payment_status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 6px;border-radius:3px;font-size:11px">{}</span>',
            colour,
            obj.get_payment_status_display(),
        )


@admin.register(SessionAttendance)
class SessionAttendanceAdmin(admin.ModelAdmin):
    list_display = ("session", "player", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("session__title", "player__email", "player__first_name")
    raw_id_fields = ("session", "player")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"


@admin.register(SessionNote)
class SessionNoteAdmin(admin.ModelAdmin):
    list_display = ("session", "author", "short_content", "created_at")
    search_fields = ("session__title", "author__email", "content")
    raw_id_fields = ("session", "author")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    @admin.display(description="Content")
    def short_content(self, obj):
        return (obj.content[:60] + "…") if len(obj.content) > 60 else obj.content

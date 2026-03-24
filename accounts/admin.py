from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from accounts.models import (
    User,
    OTP,
    FederationProfile,
    ClubProfile,
    CoachProfile,
    RefereeProfile,
    PlayerProfile,
    FanProfile,
)
from accounts.models.profiles.base import VerificationStatus


# ─── Shared bulk actions ───────────────────────────────────────


def _approve_profiles(modeladmin, request, queryset):
    queryset.update(
        verification_status=VerificationStatus.APPROVED,
        verified_by=request.user,
        verified_at=timezone.now(),
        rejection_reason="",
    )


_approve_profiles.short_description = "✔ Approve selected profiles"


def _reject_profiles(modeladmin, request, queryset):
    queryset.update(
        verification_status=VerificationStatus.REJECTED,
        verified_by=request.user,
        verified_at=timezone.now(),
    )


_reject_profiles.short_description = "✘ Reject selected profiles"


def _set_under_review(modeladmin, request, queryset):
    queryset.update(verification_status=VerificationStatus.UNDER_REVIEW)


_set_under_review.short_description = "⏳ Mark as Under Review"


# ─── OTP ──────────────────────────────────────────────────────


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("email", "type", "code", "created_at")
    list_filter = ("type",)
    search_fields = ("email",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


# ─── User ─────────────────────────────────────────────────────


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal Info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                    "photo",
                    "language",
                    "nationality",
                    "date_of_birth",
                    "bio",
                )
            },
        ),
        (
            _("Account"),
            {
                "fields": (
                    "user_type",
                    "is_active",
                    "email_verified",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "classes": ("collapse",),
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ("collapse",),
                "fields": ("last_login", "date_joined", "created_at", "updated_at"),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "user_type",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    list_display = (
        "email",
        "full_name",
        "user_type",
        "is_active",
        "email_verified",
        "profile_badge",
        "created_at",
    )
    list_display_links = ("email", "full_name")
    list_filter = ("user_type", "is_active", "email_verified")
    search_fields = ("email", "first_name", "last_name", "phone_number")
    ordering = ("-created_at",)
    readonly_fields = ("date_joined", "last_login", "created_at", "updated_at")
    date_hierarchy = "created_at"
    list_select_related = True
    list_per_page = 50

    @admin.display(description="Name")
    def full_name(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="Profile")
    def profile_badge(self, obj):
        mapping = (
            ("federation_profile", "Federation", "#1d6fa5"),
            ("club_profile", "Club", "#155724"),
            ("coach_profile", "Coach", "#856404"),
            ("referee_profile", "Referee", "#5a2d82"),
            ("player_profile", "Player", "#0c5460"),
            ("fan_profile", "Fan", "#495057"),
        )
        for attr, label, colour in mapping:
            if hasattr(obj, attr):
                return format_html(
                    '<span style="background:{};color:#fff;padding:2px 6px;'
                    'border-radius:3px;font-size:11px">{}</span>',
                    colour,
                    label,
                )
        return "—"


# ─── Profile admin base ────────────────────────────────────────


class _ProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ("user", "verified_by")
    readonly_fields = ("verified_by", "verified_at", "created_at", "updated_at")
    actions = [_approve_profiles, _reject_profiles, _set_under_review]
    list_per_page = 50
    list_select_related = True

    @admin.display(description="Status", ordering="verification_status")
    def status_badge(self, obj):
        colours = {
            VerificationStatus.PENDING: "#856404",
            VerificationStatus.UNDER_REVIEW: "#0c5460",
            VerificationStatus.APPROVED: "#155724",
            VerificationStatus.REJECTED: "#721c24",
        }
        colour = colours.get(obj.verification_status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 7px;'
            'border-radius:3px;font-size:11px">{}</span>',
            colour,
            obj.get_verification_status_display(),
        )


# ─── Federation ────────────────────────────────────────────────


@admin.register(FederationProfile)
class FederationProfileAdmin(_ProfileAdmin):
    list_display = (
        "federation_name",
        "country",
        "sport",
        "status_badge",
        "is_active",
        "created_at",
    )
    list_filter = ("verification_status", "sport", "country", "is_active")
    search_fields = ("federation_name", "contact_email", "user__email")
    date_hierarchy = "created_at"
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "federation_name",
                    "sport",
                    "country",
                    "founding_year",
                    "registration_number",
                    "description",
                )
            },
        ),
        (
            "Contact & Web",
            {"fields": ("logo", "website", "contact_email", "contact_phone")},
        ),
        (
            "Verification",
            {
                "fields": (
                    "verification_status",
                    "verified_by",
                    "verified_at",
                    "rejection_reason",
                    "is_active",
                )
            },
        ),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )


# ─── Club ─────────────────────────────────────────────────────


@admin.register(ClubProfile)
class ClubProfileAdmin(_ProfileAdmin):
    list_display = (
        "club_name",
        "club_type",
        "country",
        "city",
        "status_badge",
        "is_active",
        "created_at",
    )
    list_filter = ("club_type", "verification_status", "country", "is_active")
    search_fields = ("club_name", "city", "contact_email", "user__email")
    date_hierarchy = "created_at"
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "club_name",
                    "club_type",
                    "country",
                    "city",
                    "address",
                    "founding_year",
                    "registration_number",
                    "facility_count",
                    "description",
                )
            },
        ),
        (
            "Contact & Web",
            {"fields": ("logo", "website", "contact_email", "contact_phone")},
        ),
        (
            "Verification",
            {
                "fields": (
                    "verification_status",
                    "verified_by",
                    "verified_at",
                    "rejection_reason",
                    "is_active",
                )
            },
        ),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )


# ─── Coach ────────────────────────────────────────────────────


@admin.register(CoachProfile)
class CoachProfileAdmin(_ProfileAdmin):
    list_display = (
        "user",
        "specialization",
        "coaching_level",
        "years_experience",
        "license_number",
        "status_badge",
        "is_active",
    )
    list_filter = ("coaching_level", "verification_status", "is_active")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "license_number",
        "specialization",
    )
    date_hierarchy = "created_at"
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "coaching_level",
                    "specialization",
                    "years_experience",
                    "license_number",
                    "certifications",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "verification_status",
                    "verified_by",
                    "verified_at",
                    "rejection_reason",
                    "is_active",
                )
            },
        ),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )


# ─── Referee ──────────────────────────────────────────────────


@admin.register(RefereeProfile)
class RefereeProfileAdmin(_ProfileAdmin):
    list_display = (
        "user",
        "referee_level",
        "years_experience",
        "itf_badge",
        "license_number",
        "status_badge",
        "is_active",
    )
    list_filter = ("referee_level", "verification_status", "is_active")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "license_number",
        "itf_badge",
    )
    date_hierarchy = "created_at"
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "referee_level",
                    "years_experience",
                    "license_number",
                    "certifications",
                    "itf_badge",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "verification_status",
                    "verified_by",
                    "verified_at",
                    "rejection_reason",
                    "is_active",
                )
            },
        ),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )


# ─── Player ───────────────────────────────────────────────────


@admin.register(PlayerProfile)
class PlayerProfileAdmin(_ProfileAdmin):
    @admin.display(description="Nationality", ordering="user__nationality")
    def user_nationality(self, obj):
        return obj.user.nationality or "—"

    list_display = (
        "user",
        "skill_level",
        "dominant_hand",
        "user_nationality",
        "ranking",
        "status_badge",
        "is_active",
    )
    list_filter = ("skill_level", "dominant_hand", "verification_status", "is_active")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__nationality",
    )
    date_hierarchy = "created_at"
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "skill_level",
                    "dominant_hand",
                    "ranking",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "verification_status",
                    "verified_by",
                    "verified_at",
                    "rejection_reason",
                    "is_active",
                )
            },
        ),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )


# ─── Fan ──────────────────────────────────────────────────────


@admin.register(FanProfile)
class FanProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "user_nationality",
        "favorite_club",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__nationality",
    )
    raw_id_fields = ("user", "favorite_club")
    readonly_fields = ("verification_status", "created_at", "updated_at")
    date_hierarchy = "created_at"
    list_select_related = True
    fieldsets = (
        (
            None,
            {"fields": ("user", "favorite_club", "is_active")},
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": ("verification_status", "created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Nationality", ordering="user__nationality")
    def user_nationality(self, obj):
        return obj.user.nationality or "—"

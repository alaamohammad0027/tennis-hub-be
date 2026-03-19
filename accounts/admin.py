from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from accounts.models import User, OTP


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "type",
        "code",
        "created_at",
    )
    list_filter = ("type", "created_at")
    search_fields = ("email", "code")
    ordering = ("-created_at",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "user_type",
                    "phone_number",
                    "photo",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
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
        "first_name",
        "last_name",
        "user_type",
        "is_active",
        "created_at",
    )
    readonly_fields = (
        "date_joined",
        "last_login",
        "created_at",
        "updated_at",
    )
    list_filter = ("user_type", "is_active", "is_staff", "created_at")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)

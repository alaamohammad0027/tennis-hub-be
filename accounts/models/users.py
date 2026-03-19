from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4
from accounts.managers import UserManager
from core.services.validators import validate_model_image_only


class UserType(models.TextChoices):
    ADMIN = "ADMIN", _("Admin")
    MEMBER = "MEMBER", _("Member")


class User(AbstractUser):
    """Custom User model"""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField(_("Email Address"), unique=True, db_index=True)
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True)
    language = models.CharField(_("Language"), max_length=20, blank=True, default="en")

    photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        null=True,
        validators=[validate_model_image_only],
    )

    # User Type and Permissions
    user_type = models.CharField(
        _("User Type"),
        max_length=20,
        choices=UserType.choices,
        default=UserType.,
        db_index=True,
    )

    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    username = None
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def tokens(self) -> dict:
        refresh = RefreshToken.for_user(self)
        access_token = refresh.access_token
        return {
            "refresh": str(refresh),
            "access": str(access_token),
        }

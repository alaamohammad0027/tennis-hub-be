from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4
from django_countries.fields import CountryField
from accounts.managers import UserManager
from core.services.validators import validate_model_image_only
from accounts.models.choices import UserType


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

    user_type = models.CharField(
        _("User Type"),
        max_length=20,
        choices=UserType.choices,
        default=UserType.FAN,
        db_index=True,
    )

    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Set to False to disable the account (admin action). "
        ),
    )
    email_verified = models.BooleanField(
        _("Email Verified"),
        default=False,
        help_text=_("True once the user has confirmed their email via OTP."),
    )
    nationality = CountryField(_("Nationality"), blank=True)
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
    bio = models.TextField(_("Bio"), blank=True)
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

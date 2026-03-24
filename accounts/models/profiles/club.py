from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from .base import BaseProfile


class ClubType(models.TextChoices):
    CLUB = "club", _("Tennis Club")
    ACADEMY = "academy", _("Academy")
    TRAINING_CENTER = "training_center", _("Training Center")
    SCHOOL = "school", _("School / University")
    OTHER = "other", _("Other")


class ClubProfile(BaseProfile):
    """
    Profile for Clubs, Academies, Training Centers, and similar entities.

    Verified by: Platform Admin OR the Federation they are linked to.
    Can verify:  Coaches, Referees, Players affiliated with this club.
    Federation link is managed via tennis.Affiliation (link_type=club_federation).
    """

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="club_profile",
    )
    club_name = models.CharField(_("Club Name"), max_length=200)
    club_type = models.CharField(
        _("Type"), max_length=30, choices=ClubType.choices, default=ClubType.CLUB
    )
    country = CountryField(_("Country"), blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True)
    address = models.CharField(_("Address"), max_length=255, blank=True)
    founding_year = models.PositiveIntegerField(
        _("Founding Year"), null=True, blank=True
    )
    registration_number = models.CharField(
        _("Registration Number"), max_length=100, blank=True
    )
    logo = models.ImageField(_("Logo"), upload_to="club_logos/", blank=True, null=True)
    website = models.URLField(_("Website"), blank=True)
    contact_email = models.EmailField(_("Contact Email"), blank=True)
    contact_phone = models.CharField(_("Contact Phone"), max_length=50, blank=True)
    description = models.TextField(_("Description"), blank=True)
    facility_count = models.PositiveIntegerField(
        _("Number of Courts/Facilities"), default=0
    )

    class Meta:
        verbose_name = _("Club Profile")
        verbose_name_plural = _("Club Profiles")
        ordering = ["club_name"]

    def __str__(self):
        return f"{self.club_name} ({self.get_club_type_display()})"

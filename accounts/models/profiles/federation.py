from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from .base import BaseProfile


class FederationSport(models.TextChoices):
    TENNIS = "tennis", _("Tennis")
    MULTI_SPORT = "multi_sport", _("Multi-Sport")
    OTHER = "other", _("Other")


class FederationProfile(BaseProfile):
    """
    Profile for Sport Federations (national / international bodies).

    Verified by: Platform Admin only.
    Can verify: Clubs that link themselves to this federation.
    """

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="federation_profile",
    )
    federation_name = models.CharField(_("Federation Name"), max_length=200)
    sport = models.CharField(
        _("Sport"),
        max_length=30,
        choices=FederationSport.choices,
        default=FederationSport.TENNIS,
    )
    country = CountryField(_("Country"))
    founding_year = models.PositiveIntegerField(
        _("Founding Year"), null=True, blank=True
    )
    registration_number = models.CharField(
        _("Registration Number"), max_length=100, blank=True
    )
    logo = models.ImageField(
        _("Logo"), upload_to="federation_logos/", blank=True, null=True
    )
    website = models.URLField(_("Website"), blank=True)
    contact_email = models.EmailField(_("Contact Email"), blank=True)
    contact_phone = models.CharField(_("Contact Phone"), max_length=50, blank=True)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Federation Profile")
        verbose_name_plural = _("Federation Profiles")
        ordering = ["federation_name"]

    def __str__(self):
        return f"{self.federation_name} ({self.country})"

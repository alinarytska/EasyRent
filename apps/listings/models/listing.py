from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Listing(models.Model):
    class PropertyType(models.TextChoices):
        APARTMENT = "apartment", _("Apartment")
        HOUSE = "house", _("House")
        STUDIO = "studio", _("Studio")
        ROOM = "room", _("Room")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"))
    property_type = models.CharField(
        _("property type"),
        max_length=20,
        choices=PropertyType.choices,
        db_index=True,
    )
    price_per_night = models.DecimalField(
        _("price per night"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        db_index=True,
    )
    rooms = models.PositiveSmallIntegerField(
        _("rooms"),
        validators=[MinValueValidator(1)],
        db_index=True,
    )
    city = models.CharField(_("city"), max_length=100, db_index=True)
    district = models.CharField(
        _("district"),
        max_length=100,
        blank=True,
        db_index=True,
    )
    postal_code = models.CharField(
        _("postal code"),
        max_length=5,
        validators=[
            RegexValidator(
                regex=r"^\d{5}$",
                message="Postal code must contain exactly 5 digits.",
            )
        ],
    )
    street = models.CharField(_("street"), max_length=150)
    house_number = models.CharField(_("house number"), max_length=20)
    is_active = models.BooleanField(_("active"), default=True, db_index=True)
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Listing")
        verbose_name_plural = _("Listings")

    def __str__(self):
        return self.title

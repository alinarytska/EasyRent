from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel

from .manager import ListingManager


MIN_PRICE_PER_NIGHT = Decimal("0.01")
MIN_ROOMS = 1
MAX_ROOMS = 50


class Listing(BaseModel):
    class PropertyType(models.TextChoices):
        APARTMENT = "apartment", _("Apartment")
        HOUSE = "house", _("House")
        STUDIO = "studio", _("Studio")
        ROOM = "room", _("Room")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
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
        validators=[
            MinValueValidator(MIN_PRICE_PER_NIGHT),
        ],
        db_index=True,
    )
    rooms = models.PositiveSmallIntegerField(
        _("rooms"),
        validators=[
            MinValueValidator(MIN_ROOMS),
            MaxValueValidator(MAX_ROOMS),
        ],
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

    objects = ListingManager()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Listing")
        verbose_name_plural = _("Listings")
        constraints = (
            models.CheckConstraint(
                condition=models.Q(price_per_night__gte=MIN_PRICE_PER_NIGHT),
                name="listing_price_per_night_min",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(rooms__gte=MIN_ROOMS)
                    & models.Q(rooms__lte=MAX_ROOMS)
                ),
                name="listing_rooms_range",
            ),
        )

    def __str__(self):
        return self.title

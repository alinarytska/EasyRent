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
    """Rental property published by a landlord and available for booking."""

    class PropertyType(models.TextChoices):
        APARTMENT = "apartment", _("Apartment")
        HOUSE = "house", _("House")
        STUDIO = "studio", _("Studio")
        ROOM = "room", _("Room")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="listings",
        help_text=_("Landlord who owns this listing."),
    )
    title = models.CharField(
        _("title"),
        max_length=200,
        help_text=_("Short public title of the rental property."),
    )
    description = models.TextField(
        _("description"),
        help_text=_("Detailed public description of the rental property."),
    )
    property_type = models.CharField(
        _("property type"),
        max_length=20,
        choices=PropertyType.choices,
        db_index=True,
        help_text=_("Type of rental property."),
    )
    price_per_night = models.DecimalField(
        _("price per night"),
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(MIN_PRICE_PER_NIGHT),
        ],
        db_index=True,
        help_text=_("Current price for one night."),
    )
    rooms = models.PositiveSmallIntegerField(
        _("rooms"),
        validators=[
            MinValueValidator(MIN_ROOMS),
            MaxValueValidator(MAX_ROOMS),
        ],
        db_index=True,
        help_text=_("Number of rooms in the rental property."),
    )
    city = models.CharField(
        _("city"),
        max_length=100,
        db_index=True,
        help_text=_("City where the listing is located."),
    )
    district = models.CharField(
        _("district"),
        max_length=100,
        blank=True,
        db_index=True,
        help_text=_("District or neighborhood where the listing is located."),
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
        help_text=_("Five-digit postal code."),
    )
    street = models.CharField(
        _("street"),
        max_length=150,
        help_text=_("Street name of the rental property."),
    )
    house_number = models.CharField(
        _("house number"),
        max_length=20,
        help_text=_("House or building number of the rental property."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        db_index=True,
        help_text=_("Controls whether the listing is visible in the public catalog."),
    )

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

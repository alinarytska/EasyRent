from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel

from .manager import BookingManager


MIN_BOOKING_PRICE = Decimal("0.01")


class Booking(BaseModel):
    """Reservation request for a listing made by a renter."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        REJECTED = "rejected", _("Rejected")
        CANCELLED = "cancelled", _("Cancelled")
        COMPLETED = "completed", _("Completed")

    listing = models.ForeignKey(
        "listings.Listing",
        on_delete=models.PROTECT,
        related_name="bookings",
        help_text=_("Listing reserved by this booking."),
    )
    renter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
        help_text=_("User who created the booking."),
    )
    start_date = models.DateField(
        _("start date"),
        db_index=True,
        help_text=_("First day of the stay."),
    )
    end_date = models.DateField(
        _("end date"),
        db_index=True,
        help_text=_("Checkout date; must be after the start date."),
    )
    price_per_night = models.DecimalField(
        _("price per night"),
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(MIN_BOOKING_PRICE),
        ],
        editable=False,
        help_text=_("Snapshot of the listing price when the booking was created."),
    )
    total_price = models.DecimalField(
        _("total price"),
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(MIN_BOOKING_PRICE),
        ],
        editable=False,
        help_text=_("Total booking price calculated from dates and nightly price."),
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text=_("Current booking workflow status."),
    )

    objects = BookingManager()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Booking")
        verbose_name_plural = _("Bookings")
        constraints = (
            models.CheckConstraint(
                condition=models.Q(end_date__gt=models.F("start_date")),
                name="booking_end_after_start",
            ),
            models.CheckConstraint(
                condition=models.Q(price_per_night__gte=MIN_BOOKING_PRICE),
                name="booking_price_per_night_min",
            ),
            models.CheckConstraint(
                condition=models.Q(total_price__gte=MIN_BOOKING_PRICE),
                name="booking_total_price_min",
            ),
        )

    @property
    def number_of_nights(self):
        return (self.end_date - self.start_date).days

    def __str__(self):
        return f"{self.listing} ({self.start_date} - {self.end_date})"

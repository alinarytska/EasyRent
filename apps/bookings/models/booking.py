from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Booking(models.Model):
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
    )
    renter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    start_date = models.DateField(_("start date"), db_index=True)
    end_date = models.DateField(_("end date"), db_index=True)
    price_per_night = models.DecimalField(
        _("price per night"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        editable=False,
    )
    total_price = models.DecimalField(
        _("total price"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        editable=False,
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Booking")
        verbose_name_plural = _("Bookings")
        constraints = (
            models.CheckConstraint(
                condition=models.Q(end_date__gt=models.F("start_date")),
                name="booking_end_after_start",
            ),
        )

    @property
    def number_of_nights(self):
        return (self.end_date - self.start_date).days

    def __str__(self):
        return f"{self.listing} ({self.start_date} - {self.end_date})"

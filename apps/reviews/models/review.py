from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class Review(BaseModel):
    """Rating and optional comment left for a completed booking."""

    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.PROTECT,
        related_name="review",
        help_text=_("Completed booking this review belongs to."),
    )
    rating = models.PositiveSmallIntegerField(
        _("rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True,
        help_text=_("Rating from 1 to 5."),
    )
    comment = models.TextField(
        _("comment"),
        max_length=2000,
        blank=True,
        help_text=_("Optional text comment from the renter."),
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        constraints = (
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_between_1_and_5",
            ),
        )

    @property
    def author(self):
        return self.booking.renter

    @property
    def listing(self):
        return self.booking.listing

    def __str__(self):
        return f"Review by {self.author} for {self.listing}"

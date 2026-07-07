from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Review(models.Model):
    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.PROTECT,
        related_name="review",
    )
    rating = models.PositiveSmallIntegerField(
        _("rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True,
    )
    comment = models.TextField(_("comment"), max_length=2000, blank=True)
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

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

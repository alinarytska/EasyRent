from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ViewHistory(models.Model):
    """Last recorded view of a listing by a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="view_history",
        help_text=_("User who viewed the listing."),
    )
    listing = models.ForeignKey(
        "listings.Listing",
        on_delete=models.CASCADE,
        related_name="view_history",
        help_text=_("Listing viewed by the user."),
    )
    viewed_at = models.DateTimeField(
        _("viewed at"),
        auto_now=True,
        db_index=True,
        help_text=_("Date and time of the latest recorded view."),
    )

    class Meta:
        ordering = ("-viewed_at", "-id")
        constraints = (
            models.UniqueConstraint(
                fields=("user", "listing"),
                name="unique_user_listing_view",
            ),
        )
        verbose_name = _("View history entry")
        verbose_name_plural = _("View history entries")

    def __str__(self):
        return f"{self.user} viewed {self.listing}"

from pathlib import Path
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _


def listing_image_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    unique_filename = f"{uuid4().hex}{extension}"

    return f"listings/{instance.listing_id}/{unique_filename}"


class ListingImage(models.Model):
    listing = models.ForeignKey(
        "listings.Listing",
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        _("image"),
        upload_to=listing_image_upload_path,
    )
    is_primary = models.BooleanField(
        _("primary image"),
        default=False,
    )
    position = models.PositiveSmallIntegerField(
        _("position"),
        default=0,
    )
    uploaded_at = models.DateTimeField(
        _("uploaded at"),
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-is_primary", "position", "id")
        verbose_name = _("Listing image")
        verbose_name_plural = _("Listing images")

    def __str__(self):
        return f"Image for {self.listing}"

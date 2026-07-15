from pathlib import Path
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.listings.validators import validate_listing_image_size


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
    primary_listing = models.ForeignKey(
        "listings.Listing",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
    )
    image = models.ImageField(
        _("image"),
        upload_to=listing_image_upload_path,
        validators=[validate_listing_image_size],
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
        constraints = (
            models.UniqueConstraint(
                fields=("primary_listing",),
                name="unique_primary_image_per_listing",
            ),
        )

    def __str__(self):
        return f"Image for {self.listing}"

    def sync_primary_listing(self):
        self.primary_listing_id = self.listing_id if self.is_primary else None

    def clean(self):
        self.sync_primary_listing()
        super().clean()

    def save(self, *args, **kwargs):
        self.sync_primary_listing()
        super().save(*args, **kwargs)

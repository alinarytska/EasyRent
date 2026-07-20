from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


MAX_LISTING_IMAGE_SIZE_MB = 5
MAX_LISTING_IMAGE_SIZE_BYTES = MAX_LISTING_IMAGE_SIZE_MB * 1024 * 1024


def validate_listing_image_size(image):
    """Validate that an uploaded listing image is below the size limit."""

    if image.size > MAX_LISTING_IMAGE_SIZE_BYTES:
        raise ValidationError(
            _(
                "Image file size must not exceed "
                f"{MAX_LISTING_IMAGE_SIZE_MB} MB."
            )
        )

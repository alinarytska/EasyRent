from rest_framework import serializers

from apps.listings.models import ListingImage


class ListingImageSerializer(serializers.ModelSerializer):
    """Serializer for managing images attached to listing objects."""

    listing_title = serializers.CharField(
        source="listing.title",
        read_only=True,
        help_text="Title of the listing this image belongs to.",
    )
    listing_owner = serializers.IntegerField(
        source="listing.owner_id",
        read_only=True,
        help_text="ID of the user who owns the related listing.",
    )
    listing_owner_email = serializers.EmailField(
        source="listing.owner.email",
        read_only=True,
        help_text="Email of the related listing owner. Visible only in owner-facing responses.",
    )

    class Meta:
        model = ListingImage
        fields = (
            "id",
            "listing",
            "listing_title",
            "listing_owner",
            "listing_owner_email",
            "image",
            "is_primary",
            "position",
            "uploaded_at",
        )
        read_only_fields = (
            "id",
            "listing_title",
            "listing_owner",
            "listing_owner_email",
            "uploaded_at",
        )
        extra_kwargs = {
            "listing": {"help_text": "Listing ID to which the image belongs."},
            "image": {"help_text": "Uploaded image file for the listing."},
            "is_primary": {"help_text": "Marks this image as the main image for the listing."},
            "position": {"help_text": "Display order of the image within the listing gallery."},
        }

    def validate(self, attrs):
        listing = attrs.get(
            "listing",
            self.instance.listing if self.instance else None,
        )
        is_primary = attrs.get(
            "is_primary",
            self.instance.is_primary if self.instance else False,
        )

        if self.instance and "listing" in attrs:
            if listing != self.instance.listing:
                raise serializers.ValidationError(
                    {
                        "listing": (
                            "Listing cannot be changed after image creation."
                        )
                    }
                )

        if is_primary and listing:
            existing_primary_image = ListingImage.objects.filter(
                primary_listing=listing,
            )

            if self.instance:
                existing_primary_image = existing_primary_image.exclude(
                    pk=self.instance.pk,
                )

            if existing_primary_image.exists():
                raise serializers.ValidationError(
                    {
                        "is_primary": (
                            "This listing already has a primary image."
                        )
                    }
                )

        return attrs


class PublicListingImageSerializer(ListingImageSerializer):
    """Public image representation without listing owner email."""

    listing_owner_email = None

    class Meta(ListingImageSerializer.Meta):
        fields = tuple(
            field
            for field in ListingImageSerializer.Meta.fields
            if field != "listing_owner_email"
        )
        read_only_fields = tuple(
            field
            for field in ListingImageSerializer.Meta.read_only_fields
            if field != "listing_owner_email"
        )

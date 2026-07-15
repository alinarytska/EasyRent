from rest_framework import serializers

from apps.listings.models import ListingImage


class ListingImageSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source="listing.title", read_only=True)
    listing_owner = serializers.IntegerField(source="listing.owner_id", read_only=True)
    listing_owner_email = serializers.EmailField(
        source="listing.owner.email",
        read_only=True,
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

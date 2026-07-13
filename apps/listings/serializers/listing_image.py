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

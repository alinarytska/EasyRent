from rest_framework import serializers

from apps.listings.models import ListingImage


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = (
            "id",
            "listing",
            "image",
            "is_primary",
            "position",
            "uploaded_at",
        )
        read_only_fields = ("id", "uploaded_at")

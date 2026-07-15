from rest_framework import serializers

from apps.listings.models import Listing
from apps.listings.serializers.listing_image import ListingImageSerializer


class ListingSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    images = ListingImageSerializer(many=True, read_only=True)
    views_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Listing
        fields = (
            "id",
            "owner",
            "owner_email",
            "title",
            "description",
            "property_type",
            "price_per_night",
            "rooms",
            "city",
            "district",
            "postal_code",
            "street",
            "house_number",
            "is_active",
            "images",
            "views_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "owner",
            "owner_email",
            "images",
            "views_count",
            "created_at",
            "updated_at",
        )

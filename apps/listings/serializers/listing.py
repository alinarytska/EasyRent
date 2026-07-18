from rest_framework import serializers

from apps.listings.models import Listing
from apps.listings.serializers.listing_image import (
    ListingImageSerializer,
    PublicListingImageSerializer,
)


class ListingSerializer(serializers.ModelSerializer):
    """Full listing representation used for owners and write operations."""

    owner = serializers.PrimaryKeyRelatedField(
        read_only=True,
        help_text="ID of the landlord who owns the listing.",
    )
    owner_email = serializers.EmailField(
        source="owner.email",
        read_only=True,
        help_text="Email of the listing owner. Visible only in owner-facing responses.",
    )
    images = ListingImageSerializer(
        many=True,
        read_only=True,
        help_text="Images attached to the listing.",
    )
    views_count = serializers.IntegerField(
        read_only=True,
        help_text="Number of recorded authenticated user views.",
    )

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
        extra_kwargs = {
            "title": {"help_text": "Short public title of the rental listing."},
            "description": {"help_text": "Detailed public description of the property."},
            "property_type": {"help_text": "Type of property: apartment, house, studio or room."},
            "price_per_night": {"help_text": "Price for one night in the listing currency."},
            "rooms": {"help_text": "Number of rooms available in the property."},
            "city": {"help_text": "City where the property is located."},
            "district": {"help_text": "Optional city district or neighborhood."},
            "postal_code": {"help_text": "Five-digit postal code."},
            "street": {"help_text": "Street name of the property."},
            "house_number": {"help_text": "House number of the property."},
            "is_active": {"help_text": "Whether the listing is publicly visible and bookable."},
        }

    def validate(self, attrs):
        if (
            self.instance
            and self.instance.is_active
            and attrs.get("is_active") is False
        ):
            from apps.bookings.models import Booking

            has_active_bookings = self.instance.bookings.filter(
                status__in=(
                    Booking.Status.PENDING,
                    Booking.Status.CONFIRMED,
                )
            ).exists()

            if has_active_bookings:
                raise serializers.ValidationError(
                    {
                        "is_active": (
                            "Listing cannot be deactivated while it has "
                            "pending or confirmed bookings."
                        )
                    }
                )

        return attrs


class PublicListingSerializer(ListingSerializer):
    """Public listing representation without the owner's email address."""

    owner_email = None
    images = PublicListingImageSerializer(many=True, read_only=True)

    class Meta(ListingSerializer.Meta):
        fields = tuple(
            field
            for field in ListingSerializer.Meta.fields
            if field != "owner_email"
        )
        read_only_fields = tuple(
            field
            for field in ListingSerializer.Meta.read_only_fields
            if field != "owner_email"
        )

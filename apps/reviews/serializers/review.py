from rest_framework import serializers

from apps.bookings.models import Booking
from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for renter reviews created for completed bookings."""

    booking = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.completed(),
        help_text="Completed booking ID being reviewed.",
    )
    author = serializers.IntegerField(
        source="author.id",
        read_only=True,
        help_text="ID of the renter who wrote the review.",
    )
    author_email = serializers.EmailField(
        source="author.email",
        read_only=True,
        help_text="Email of the renter who wrote the review.",
    )
    listing = serializers.IntegerField(
        source="listing.id",
        read_only=True,
        help_text="ID of the reviewed listing.",
    )
    listing_title = serializers.CharField(
        source="listing.title",
        read_only=True,
        help_text="Title of the reviewed listing.",
    )

    class Meta:
        model = Review
        fields = (
            "id",
            "booking",
            "author",
            "author_email",
            "listing",
            "listing_title",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "author",
            "author_email",
            "listing",
            "listing_title",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "rating": {"help_text": "Rating from 1 to 5."},
            "comment": {"help_text": "Optional text comment about the stay."},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        booking = attrs.get(
            "booking",
            self.instance.booking if self.instance else None,
        )

        if self.instance and "booking" in attrs:
            if booking != self.instance.booking:
                raise serializers.ValidationError(
                    {
                        "booking": (
                            "Booking cannot be changed after review creation."
                        )
                    }
                )

        if not self.instance and request:
            if booking.renter_id != request.user.id:
                raise serializers.ValidationError(
                    {
                        "booking": (
                            "You can review only your own completed bookings."
                        )
                    }
                )

        return attrs

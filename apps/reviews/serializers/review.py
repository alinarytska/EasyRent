from rest_framework import serializers

from apps.bookings.models import Booking
from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.completed(),
    )
    author = serializers.IntegerField(source="author.id", read_only=True)
    author_email = serializers.EmailField(source="author.email", read_only=True)
    listing = serializers.IntegerField(source="listing.id", read_only=True)
    listing_title = serializers.CharField(source="listing.title", read_only=True)

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

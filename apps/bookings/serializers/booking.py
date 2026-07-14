from django.utils import timezone
from rest_framework import serializers

from apps.bookings.models import Booking
from apps.bookings.services import calculate_booking_prices
from apps.listings.models import Listing


class BookingSerializer(serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.active(),
    )
    listing_title = serializers.CharField(source="listing.title", read_only=True)
    listing_owner = serializers.IntegerField(
        source="listing.owner_id",
        read_only=True,
    )
    listing_owner_email = serializers.EmailField(
        source="listing.owner.email",
        read_only=True,
    )
    renter = serializers.PrimaryKeyRelatedField(read_only=True)
    renter_email = serializers.EmailField(source="renter.email", read_only=True)
    number_of_nights = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id",
            "listing",
            "listing_title",
            "listing_owner",
            "listing_owner_email",
            "renter",
            "renter_email",
            "start_date",
            "end_date",
            "number_of_nights",
            "price_per_night",
            "total_price",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "listing_title",
            "listing_owner",
            "listing_owner_email",
            "renter",
            "renter_email",
            "number_of_nights",
            "price_per_night",
            "total_price",
            "status",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        listing = attrs.get(
            "listing",
            self.instance.listing if self.instance else None,
        )
        start_date = attrs.get(
            "start_date",
            self.instance.start_date if self.instance else None,
        )
        end_date = attrs.get(
            "end_date",
            self.instance.end_date if self.instance else None,
        )

        if start_date and end_date:
            calculate_booking_prices(
                listing=listing,
                start_date=start_date,
                end_date=end_date,
            )

        if start_date and start_date < timezone.localdate():
            raise serializers.ValidationError(
                {"start_date": "Start date cannot be in the past."}
            )

        request = self.context.get("request")

        if not self.instance and request and listing:
            if listing.owner_id == request.user.id:
                raise serializers.ValidationError(
                    {"listing": "You cannot book your own listing."}
                )

        if listing and start_date and end_date:
            overlapping_bookings = (
                Booking.objects.blocking()
                .for_listing(listing)
                .overlapping(start_date, end_date)
            )

            if self.instance:
                overlapping_bookings = overlapping_bookings.exclude(
                    pk=self.instance.pk,
                )

            if overlapping_bookings.exists():
                raise serializers.ValidationError(
                    "This listing is already booked for the selected dates."
                )

        return attrs

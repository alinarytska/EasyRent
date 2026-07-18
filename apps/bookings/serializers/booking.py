from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.bookings.models import Booking
from apps.bookings.services import calculate_booking_prices
from apps.listings.models import Listing


MAX_BOOKING_DAYS_AHEAD = 365


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for creating, viewing and updating booking requests."""

    listing = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.active(),
        help_text="ID of the active listing to book.",
    )
    listing_title = serializers.CharField(
        source="listing.title",
        read_only=True,
        help_text="Title of the booked listing.",
    )
    listing_owner = serializers.IntegerField(
        source="listing.owner_id",
        read_only=True,
        help_text="ID of the landlord who owns the booked listing.",
    )
    listing_owner_email = serializers.EmailField(
        source="listing.owner.email",
        read_only=True,
        help_text="Email of the landlord who owns the booked listing.",
    )
    renter = serializers.PrimaryKeyRelatedField(
        read_only=True,
        help_text="ID of the user who created the booking.",
    )
    renter_email = serializers.EmailField(
        source="renter.email",
        read_only=True,
        help_text="Email of the user who created the booking.",
    )
    number_of_nights = serializers.IntegerField(
        read_only=True,
        help_text="Calculated number of nights between start and end date.",
    )

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
        extra_kwargs = {
            "start_date": {
                "help_text": (
                    "First day of the stay. It cannot be in the past or more "
                    f"than {MAX_BOOKING_DAYS_AHEAD} days ahead."
                )
            },
            "end_date": {"help_text": "Checkout date. Must be after start_date."},
            "price_per_night": {"help_text": "Snapshot of listing price at booking time."},
            "total_price": {"help_text": "Calculated total booking price."},
            "status": {"help_text": "Current booking workflow status."},
        }

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

        if self.instance and "listing" in attrs:
            if listing != self.instance.listing:
                raise serializers.ValidationError(
                    {
                        "listing": (
                            "Listing cannot be changed after booking creation."
                        )
                    }
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

        latest_start_date = timezone.localdate() + timedelta(
            days=MAX_BOOKING_DAYS_AHEAD,
        )

        if start_date and start_date > latest_start_date:
            raise serializers.ValidationError(
                {
                    "start_date": (
                        "Start date cannot be more than "
                        f"{MAX_BOOKING_DAYS_AHEAD} days ahead."
                    )
                }
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

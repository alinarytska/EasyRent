from datetime import timedelta
import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError as APIValidationError

from apps.bookings.models import Booking
from apps.listings.models import Listing


logger = logging.getLogger(__name__)


def calculate_booking_prices(listing, start_date, end_date):
    """
    Calculate immutable booking price snapshots from listing and dates.

    The booking stores price_per_night and total_price separately so later
    listing price changes do not affect already created bookings.
    """

    number_of_nights = (end_date - start_date).days

    if number_of_nights <= 0:
        raise ValidationError("End date must be after start date.")

    price_per_night = listing.price_per_night
    total_price = price_per_night * number_of_nights

    return price_per_night, total_price


def validate_booking_dates_are_available(
    listing,
    start_date,
    end_date,
    exclude_booking_id=None,
):
    """
    Raise an API validation error when selected dates overlap bookings.

    Pending and confirmed bookings are treated as blocking because both reserve
    listing dates. The queryset uses row locking inside transactions to reduce
    the risk of concurrent double-booking.
    """

    overlapping_bookings = (
        Booking.objects.blocking()
        .select_for_update()
        .for_listing(listing)
        .overlapping(start_date, end_date)
    )

    if exclude_booking_id:
        overlapping_bookings = overlapping_bookings.exclude(
            pk=exclude_booking_id,
        )

    if overlapping_bookings.exists():
        logger.warning(
            "Booking date overlap detected for listing_id=%s",
            listing.pk,
        )
        raise APIValidationError(
            {
                "non_field_errors": (
                    "This listing is already booked "
                    "for the selected dates."
                )
            }
        )


@transaction.atomic
def create_booking(serializer, renter):
    """
    Create a booking inside a transaction and store price snapshots.

    The related listing is locked before availability is checked. This keeps the
    date-overlap check and booking creation in one atomic operation.
    """

    listing = serializer.validated_data["listing"]
    start_date = serializer.validated_data["start_date"]
    end_date = serializer.validated_data["end_date"]
    locked_listing = Listing.objects.select_for_update().get(pk=listing.pk)

    validate_booking_dates_are_available(
        listing=locked_listing,
        start_date=start_date,
        end_date=end_date,
    )
    price_per_night, total_price = calculate_booking_prices(
        listing=locked_listing,
        start_date=start_date,
        end_date=end_date,
    )

    booking = serializer.save(
        renter=renter,
        listing=locked_listing,
        price_per_night=price_per_night,
        total_price=total_price,
    )
    logger.info(
        "Booking created: booking_id=%s listing_id=%s renter_id=%s",
        booking.pk,
        locked_listing.pk,
        renter.pk,
    )
    return booking


@transaction.atomic
def update_booking(serializer):
    """
    Update a pending booking while preserving availability guarantees.

    Only pending bookings can be changed. Dates are rechecked against blocking
    bookings and price snapshots are recalculated from the locked listing.
    """

    if serializer.instance.status != Booking.Status.PENDING:
        raise APIValidationError(
            {"status": "Only pending bookings can be updated."}
        )

    listing = serializer.validated_data.get(
        "listing",
        serializer.instance.listing,
    )
    start_date = serializer.validated_data.get(
        "start_date",
        serializer.instance.start_date,
    )
    end_date = serializer.validated_data.get(
        "end_date",
        serializer.instance.end_date,
    )
    locked_listing = Listing.objects.select_for_update().get(pk=listing.pk)

    validate_booking_dates_are_available(
        listing=locked_listing,
        start_date=start_date,
        end_date=end_date,
        exclude_booking_id=serializer.instance.pk,
    )
    price_per_night, total_price = calculate_booking_prices(
        listing=locked_listing,
        start_date=start_date,
        end_date=end_date,
    )

    booking = serializer.save(
        listing=locked_listing,
        price_per_night=price_per_night,
        total_price=total_price,
    )
    logger.info(
        "Booking updated: booking_id=%s listing_id=%s",
        booking.pk,
        locked_listing.pk,
    )
    return booking


def update_booking_status(
    booking,
    new_status,
    allowed_statuses,
    error_message,
):
    """
    Move a booking to a new status when the transition is allowed.

    Status changes go through this helper so confirm, reject and cancel actions
    follow the same validation and logging path.
    """

    if booking.status not in allowed_statuses:
        raise APIValidationError({"status": error_message})

    booking.status = new_status
    booking.save(update_fields=("status", "updated_at"))
    logger.info(
        "Booking status changed: booking_id=%s new_status=%s",
        booking.pk,
        new_status,
    )

    return booking


def confirm_booking(booking):
    """Confirm a pending booking."""

    return update_booking_status(
        booking=booking,
        new_status=Booking.Status.CONFIRMED,
        allowed_statuses=(Booking.Status.PENDING,),
        error_message="Only pending bookings can be confirmed.",
    )


def reject_booking(booking):
    """Reject a pending booking."""

    return update_booking_status(
        booking=booking,
        new_status=Booking.Status.REJECTED,
        allowed_statuses=(Booking.Status.PENDING,),
        error_message="Only pending bookings can be rejected.",
    )


def validate_renter_cancellation_deadline(booking, user):
    """
    Ensure renters cancel bookings at least 24 hours before start date.

    Staff users and listing owners are allowed to bypass this renter deadline,
    because their cancellation flow is treated as administrative management.
    """

    if user.is_staff:
        return

    if booking.listing.owner_id == user.id:
        return

    cancellation_deadline = booking.start_date - timedelta(days=1)

    if timezone.localdate() > cancellation_deadline:
        raise APIValidationError(
            {
                "status": (
                    "Renter can cancel a booking only at least "
                    "24 hours before the start date."
                )
            }
        )


def cancel_booking(booking, user):
    """Cancel a pending or confirmed booking when the user is allowed."""

    validate_renter_cancellation_deadline(booking=booking, user=user)

    return update_booking_status(
        booking=booking,
        new_status=Booking.Status.CANCELLED,
        allowed_statuses=(
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
        ),
        error_message="Only pending or confirmed bookings can be cancelled.",
    )

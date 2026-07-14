from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.bookings.filters import BookingFilter
from apps.bookings.models import Booking
from apps.bookings.permissions import BookingPermission
from apps.bookings.serializers import BookingSerializer
from apps.bookings.services import calculate_booking_prices
from apps.listings.models import Listing


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = (BookingPermission,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = BookingFilter
    ordering_fields = (
        "start_date",
        "end_date",
        "created_at",
        "total_price",
    )
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = Booking.objects.select_related(
            "listing",
            "listing__owner",
            "renter",
        )
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.is_staff:
            return queryset

        return queryset.filter(
            Q(renter=user) | Q(listing__owner=user),
        ).distinct()

    @action(detail=False, methods=("get",), url_path="my")
    def my_bookings(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().for_renter(request.user),
        )
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def validate_booking_dates_are_available(
        self,
        listing,
        start_date,
        end_date,
        exclude_booking_id=None,
    ):
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
            raise ValidationError(
                {
                    "non_field_errors": (
                        "This listing is already booked "
                        "for the selected dates."
                    )
                }
            )

    def get_locked_booking(self):
        queryset = self.filter_queryset(
            self.get_queryset().select_for_update(),
        )
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        booking = get_object_or_404(
            queryset,
            **{self.lookup_field: lookup_value},
        )
        self.check_object_permissions(self.request, booking)
        return booking

    def update_booking_status(
        self,
        booking,
        new_status,
        allowed_statuses,
        error_message,
    ):
        if booking.status not in allowed_statuses:
            raise ValidationError({"status": error_message})

        booking.status = new_status
        booking.save(update_fields=("status", "updated_at"))
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    def validate_renter_cancellation_deadline(self, booking):
        if self.request.user.is_staff:
            return

        if booking.listing.owner_id == self.request.user.id:
            return

        cancellation_deadline = booking.start_date - timedelta(days=1)

        if timezone.localdate() > cancellation_deadline:
            raise ValidationError(
                {
                    "status": (
                        "Renter can cancel a booking only at least "
                        "24 hours before the start date."
                    )
                }
            )

    @transaction.atomic
    @action(detail=True, methods=("post",), url_path="confirm")
    def confirm(self, request, pk=None):
        booking = self.get_locked_booking()
        return self.update_booking_status(
            booking=booking,
            new_status=Booking.Status.CONFIRMED,
            allowed_statuses=(Booking.Status.PENDING,),
            error_message="Only pending bookings can be confirmed.",
        )

    @transaction.atomic
    @action(detail=True, methods=("post",), url_path="reject")
    def reject(self, request, pk=None):
        booking = self.get_locked_booking()
        return self.update_booking_status(
            booking=booking,
            new_status=Booking.Status.REJECTED,
            allowed_statuses=(Booking.Status.PENDING,),
            error_message="Only pending bookings can be rejected.",
        )

    @transaction.atomic
    @action(detail=True, methods=("post",), url_path="cancel")
    def cancel(self, request, pk=None):
        booking = self.get_locked_booking()
        self.validate_renter_cancellation_deadline(booking)
        return self.update_booking_status(
            booking=booking,
            new_status=Booking.Status.CANCELLED,
            allowed_statuses=(
                Booking.Status.PENDING,
                Booking.Status.CONFIRMED,
            ),
            error_message=(
                "Only pending or confirmed bookings can be cancelled."
            ),
        )

    @transaction.atomic
    def perform_create(self, serializer):
        listing = serializer.validated_data["listing"]
        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]
        locked_listing = Listing.objects.select_for_update().get(
            pk=listing.pk,
        )
        self.validate_booking_dates_are_available(
            listing=locked_listing,
            start_date=start_date,
            end_date=end_date,
        )
        price_per_night, total_price = calculate_booking_prices(
            listing=locked_listing,
            start_date=start_date,
            end_date=end_date,
        )

        serializer.save(
            renter=self.request.user,
            listing=locked_listing,
            price_per_night=price_per_night,
            total_price=total_price,
        )

    @transaction.atomic
    def perform_update(self, serializer):
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
        locked_listing = Listing.objects.select_for_update().get(
            pk=listing.pk,
        )
        self.validate_booking_dates_are_available(
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

        serializer.save(
            listing=locked_listing,
            price_per_night=price_per_night,
            total_price=total_price,
        )

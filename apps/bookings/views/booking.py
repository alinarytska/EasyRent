from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.bookings.filters import BookingFilter
from apps.bookings.models import Booking
from apps.bookings.permissions import BookingPermission
from apps.bookings.serializers import BookingSerializer
from apps.bookings.services import (
    cancel_booking,
    confirm_booking,
    create_booking,
    reject_booking,
    update_booking,
)


@extend_schema_view(
    list=extend_schema(
        summary="List bookings",
        description="Return bookings where the current user is renter or listing owner.",
    ),
    retrieve=extend_schema(
        summary="Retrieve booking",
        description="Return one booking visible to the current renter or listing owner.",
    ),
    create=extend_schema(
        summary="Create booking",
        description="Create a pending booking for an active listing.",
    ),
    update=extend_schema(
        summary="Replace pending booking",
        description=(
            "Replace dates for a pending booking. Only the booking renter can "
            "edit dates. Confirmed and completed bookings cannot be edited."
        ),
    ),
    partial_update=extend_schema(
        summary="Update pending booking",
        description=(
            "Partially update dates for a pending booking. Only the booking "
            "renter can edit dates."
        ),
    ),
)
class BookingViewSet(viewsets.ModelViewSet):
    """API endpoints for booking creation, visibility and status transitions."""

    serializer_class = BookingSerializer
    permission_classes = (BookingPermission,)
    http_method_names = ("get", "post", "put", "patch", "head", "options")
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

        return queryset.filter(
            Q(renter=user) | Q(listing__owner=user),
        ).distinct()

    @extend_schema(
        summary="List my bookings",
        description="Return bookings created by the authenticated renter.",
    )
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

    @transaction.atomic
    @extend_schema(
        summary="Confirm booking",
        description="Change a pending booking to confirmed. Only the listing owner can confirm.",
    )
    @action(detail=True, methods=("post",), url_path="confirm")
    def confirm(self, request, pk=None):
        booking = self.get_locked_booking()
        booking = confirm_booking(booking)
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @transaction.atomic
    @extend_schema(
        summary="Reject booking",
        description="Change a pending booking to rejected. Only the listing owner can reject.",
    )
    @action(detail=True, methods=("post",), url_path="reject")
    def reject(self, request, pk=None):
        booking = self.get_locked_booking()
        booking = reject_booking(booking)
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @transaction.atomic
    @extend_schema(
        summary="Cancel booking",
        description="Cancel a pending or confirmed booking if the user is allowed to do so.",
    )
    @action(detail=True, methods=("post",), url_path="cancel")
    def cancel(self, request, pk=None):
        booking = self.get_locked_booking()
        booking = cancel_booking(booking=booking, user=request.user)
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    def perform_create(self, serializer):
        create_booking(serializer=serializer, renter=self.request.user)

    def perform_update(self, serializer):
        update_booking(serializer=serializer)

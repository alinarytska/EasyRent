from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.bookings.filters import BookingFilter
from apps.bookings.models import Booking
from apps.bookings.serializers import BookingSerializer
from apps.bookings.services import calculate_booking_prices


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
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

    @transaction.atomic
    def perform_create(self, serializer):
        listing = serializer.validated_data["listing"]
        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]
        price_per_night, total_price = calculate_booking_prices(
            listing=listing,
            start_date=start_date,
            end_date=end_date,
        )

        serializer.save(
            renter=self.request.user,
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
        price_per_night, total_price = calculate_booking_prices(
            listing=listing,
            start_date=start_date,
            end_date=end_date,
        )

        serializer.save(
            price_per_night=price_per_night,
            total_price=total_price,
        )

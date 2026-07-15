import django_filters

from apps.bookings.models import Booking


class BookingFilter(django_filters.FilterSet):
    start_after = django_filters.DateFilter(
        field_name="start_date",
        lookup_expr="gte",
    )
    start_before = django_filters.DateFilter(
        field_name="start_date",
        lookup_expr="lte",
    )
    end_after = django_filters.DateFilter(
        field_name="end_date",
        lookup_expr="gte",
    )
    end_before = django_filters.DateFilter(
        field_name="end_date",
        lookup_expr="lte",
    )
    min_total_price = django_filters.NumberFilter(
        field_name="total_price",
        lookup_expr="gte",
    )
    max_total_price = django_filters.NumberFilter(
        field_name="total_price",
        lookup_expr="lte",
    )

    class Meta:
        model = Booking
        fields = (
            "status",
            "listing",
            "renter",
            "start_date",
            "end_date",
            "start_after",
            "start_before",
            "end_after",
            "end_before",
            "min_total_price",
            "max_total_price",
        )

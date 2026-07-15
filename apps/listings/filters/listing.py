import django_filters

from apps.listings.models import Listing


class ListingFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
        field_name="price_per_night",
        lookup_expr="gte",
    )
    max_price = django_filters.NumberFilter(
        field_name="price_per_night",
        lookup_expr="lte",
    )
    min_rooms = django_filters.NumberFilter(
        field_name="rooms",
        lookup_expr="gte",
    )
    max_rooms = django_filters.NumberFilter(
        field_name="rooms",
        lookup_expr="lte",
    )
    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
    )

    class Meta:
        model = Listing
        fields = (
            "city",
            "district",
            "street",
            "postal_code",
            "property_type",
            "rooms",
            "min_rooms",
            "max_rooms",
            "is_active",
            "min_price",
            "max_price",
            "created_after",
            "created_before",
        )

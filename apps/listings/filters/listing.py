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
            "property_type",
            "rooms",
            "is_active",
            "min_price",
            "max_price",
            "created_after",
            "created_before",
        )

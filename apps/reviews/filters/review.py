import django_filters

from apps.reviews.models import Review


class ReviewFilter(django_filters.FilterSet):
    """Filter reviews by rating, booking, listing, author and creation date."""

    min_rating = django_filters.NumberFilter(
        field_name="rating",
        lookup_expr="gte",
    )
    max_rating = django_filters.NumberFilter(
        field_name="rating",
        lookup_expr="lte",
    )
    listing = django_filters.NumberFilter(
        field_name="booking__listing",
    )
    author = django_filters.NumberFilter(
        field_name="booking__renter",
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
        model = Review
        fields = (
            "rating",
            "booking",
            "listing",
            "author",
            "min_rating",
            "max_rating",
            "created_after",
            "created_before",
        )

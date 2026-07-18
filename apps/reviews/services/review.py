from apps.reviews.models import Review


def get_reviews_for_listing(listing):
    """Return optimized reviews queryset for a specific listing."""

    return (
        Review.objects.select_related(
            "booking",
            "booking__listing",
            "booking__renter",
        )
        .filter(booking__listing=listing)
        .order_by("-created_at", "-id")
    )

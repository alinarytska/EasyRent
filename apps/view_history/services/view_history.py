from django.db.models import Count


def get_popular_listings(active_only=False, only_with_views=False):
    from apps.listings.models import Listing

    queryset = Listing.objects.active() if active_only else Listing.objects.all()
    queryset = (
        queryset
        .select_related("owner")
        .prefetch_related("images")
        .annotate(views_count=Count("view_history"))
    )

    if only_with_views:
        queryset = queryset.filter(views_count__gt=0)

    return queryset.order_by("-views_count", "-created_at")


def record_listing_view(user, listing, return_created=False):
    if not user.is_authenticated:
        return None

    from apps.view_history.models import ViewHistory

    view_history, created = ViewHistory.objects.update_or_create(
        user=user,
        listing=listing,
        defaults={},
    )

    if return_created:
        return view_history, created

    return view_history

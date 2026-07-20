import logging

from django.db.models import Count


logger = logging.getLogger(__name__)


def get_popular_listings(active_only=False, only_with_views=False):
    """
    Return listings annotated and ordered by authenticated view count.

    View popularity is calculated from ViewHistory records, so only
    authenticated user views contribute to the ranking.
    """

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
    """
    Create or refresh a view-history entry for an authenticated user.

    One record is kept per user and listing. Repeated views update viewed_at
    instead of creating duplicates, which keeps history compact.
    """

    if not user.is_authenticated:
        return None

    from apps.view_history.models import ViewHistory

    view_history, created = ViewHistory.objects.update_or_create(
        user=user,
        listing=listing,
        defaults={},
    )
    logger.debug(
        "View history recorded: view_history_id=%s "
        "user_id=%s listing_id=%s created=%s",
        view_history.pk,
        user.pk,
        listing.pk,
        created,
    )

    if return_created:
        return view_history, created

    return view_history

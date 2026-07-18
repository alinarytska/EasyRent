import logging

from django.db.models import Count


logger = logging.getLogger(__name__)


IGNORED_SEARCH_HISTORY_PARAMS = {
    "format",
    "ordering",
    "page",
    "page_size",
    "search",
}


def build_search_filters(query_params):
    """
    Build a JSON-safe filter snapshot from listing query parameters.

    Technical parameters such as pagination, ordering and the search keyword are
    ignored. The result stores only meaningful filters used with the search.
    """

    search_filters = {}

    for key in query_params:
        if key in IGNORED_SEARCH_HISTORY_PARAMS:
            continue

        values = [
            value
            for value in query_params.getlist(key)
            if value not in ("", None)
        ]

        if not values:
            continue

        search_filters[key] = values[0] if len(values) == 1 else values

    return search_filters


def record_listing_search(user, query_params):
    """
    Save an authenticated user's keyword listing search.

    Anonymous users are ignored. Searches without a non-empty keyword are also
    ignored, because popular search statistics are based on actual query text.
    """

    if not user.is_authenticated:
        return None

    query = query_params.get("search", "").strip()

    if not query:
        return None

    from apps.search_history.models import SearchHistory

    search_history = SearchHistory.objects.create(
        user=user,
        query=query,
        search_filters=build_search_filters(query_params),
    )
    logger.debug(
        "Search history recorded: search_history_id=%s user_id=%s",
        search_history.pk,
        user.pk,
    )
    return search_history


def get_popular_search_queries():
    """
    Return search keywords ordered by how often they were recorded.

    The queryset groups history rows by query text and exposes search_count for
    popular-search endpoints.
    """

    from apps.search_history.models import SearchHistory

    return (
        SearchHistory.objects.values("query")
        .annotate(search_count=Count("id"))
        .order_by("-search_count", "query")
    )

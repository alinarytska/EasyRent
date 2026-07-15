IGNORED_SEARCH_HISTORY_PARAMS = {
    "format",
    "ordering",
    "page",
    "page_size",
    "search",
}


def build_search_filters(query_params):
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
    if not user.is_authenticated:
        return None

    query = query_params.get("search", "").strip()

    if not query:
        return None

    from apps.search_history.models import SearchHistory

    return SearchHistory.objects.create(
        user=user,
        query=query,
        search_filters=build_search_filters(query_params),
    )

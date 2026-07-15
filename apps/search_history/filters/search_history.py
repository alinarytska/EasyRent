import django_filters

from apps.search_history.models import SearchHistory


class SearchHistoryFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(
        field_name="query",
        lookup_expr="icontains",
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
        model = SearchHistory
        fields = (
            "query",
            "created_after",
            "created_before",
        )

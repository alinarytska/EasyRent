import django_filters

from apps.view_history.models import ViewHistory


class ViewHistoryFilter(django_filters.FilterSet):
    viewed_after = django_filters.DateTimeFilter(
        field_name="viewed_at",
        lookup_expr="gte",
    )
    viewed_before = django_filters.DateTimeFilter(
        field_name="viewed_at",
        lookup_expr="lte",
    )

    class Meta:
        model = ViewHistory
        fields = (
            "listing",
            "viewed_after",
            "viewed_before",
        )

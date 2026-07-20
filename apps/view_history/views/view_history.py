from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from apps.view_history.filters import ViewHistoryFilter
from apps.view_history.models import ViewHistory
from apps.view_history.serializers import ViewHistorySerializer


@extend_schema_view(
    list=extend_schema(
        summary="List view history",
        description="Return listing views automatically saved for the authenticated user.",
    ),
    retrieve=extend_schema(
        summary="Retrieve view history entry",
        description="Return one view history entry owned by the authenticated user.",
    ),
)
class ViewHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoints for the current user's listing view history."""

    serializer_class = ViewHistorySerializer
    throttle_scope = "history"
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = ViewHistoryFilter
    ordering_fields = (
        "viewed_at",
        "listing",
        "id",
    )
    ordering = ("-viewed_at", "-id")

    def get_queryset(self):
        queryset = ViewHistory.objects.select_related("user", "listing")

        if not self.request.user.is_authenticated:
            return queryset.none()

        return queryset.filter(user=self.request.user)

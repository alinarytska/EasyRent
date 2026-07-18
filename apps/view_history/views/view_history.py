from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.listings.serializers import PublicListingSerializer
from apps.view_history.filters import ViewHistoryFilter
from apps.view_history.models import ViewHistory
from apps.view_history.serializers import ViewHistorySerializer
from apps.view_history.services import get_popular_listings


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
    """Read-only endpoints for view history and popular listings."""

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

    @extend_schema(
        summary="List popular viewed listings",
        description="Return active listings ordered by authenticated users' view count.",
        responses=PublicListingSerializer(many=True),
    )
    @action(
        detail=False,
        methods=("get",),
        url_path="popular-listings",
        throttle_scope="popular",
    )
    def popular_listings(self, request):
        queryset = get_popular_listings(
            active_only=True,
            only_with_views=True,
        )
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = PublicListingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PublicListingSerializer(queryset, many=True)
        return Response(serializer.data)

from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.search_history.filters import SearchHistoryFilter
from apps.search_history.models import SearchHistory
from apps.search_history.serializers import (
    PopularSearchQuerySerializer,
    SearchHistorySerializer,
)
from apps.search_history.services import get_popular_search_queries


@extend_schema_view(
    list=extend_schema(
        summary="List search history",
        description="Return keyword searches automatically saved for the authenticated user.",
    ),
    retrieve=extend_schema(
        summary="Retrieve search history entry",
        description="Return one search history entry owned by the authenticated user.",
    ),
)
class SearchHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoints for search history and popular search queries."""

    serializer_class = SearchHistorySerializer
    throttle_scope = "history"
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = SearchHistoryFilter
    ordering_fields = (
        "query",
        "created_at",
        "id",
    )
    ordering = ("-created_at", "-id")

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return SearchHistory.objects.none()

        return SearchHistory.objects.filter(user=self.request.user)

    @extend_schema(
        summary="List popular search queries",
        description="Return keyword queries ordered by search frequency.",
        responses=PopularSearchQuerySerializer(many=True),
    )
    @action(
        detail=False,
        methods=("get",),
        url_path="popular",
        throttle_scope="popular",
    )
    def popular_queries(self, request):
        queryset = get_popular_search_queries()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = PopularSearchQuerySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PopularSearchQuerySerializer(queryset, many=True)
        return Response(serializer.data)

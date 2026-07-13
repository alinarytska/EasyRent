from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.search_history.models import SearchHistory
from apps.search_history.serializers import (
    PopularSearchQuerySerializer,
    SearchHistorySerializer,
)


class SearchHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = SearchHistorySerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return SearchHistory.objects.none()

        return SearchHistory.objects.filter(user=self.request.user)

    @extend_schema(responses=PopularSearchQuerySerializer(many=True))
    @action(detail=False, methods=("get",), url_path="popular")
    def popular_queries(self, request):
        queryset = (
            SearchHistory.objects.values("query")
            .annotate(search_count=Count("id"))
            .order_by("-search_count", "query")
        )
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = PopularSearchQuerySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PopularSearchQuerySerializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

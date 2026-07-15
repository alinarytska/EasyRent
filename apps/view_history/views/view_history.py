from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.listings.serializers import ListingSerializer
from apps.view_history.filters import ViewHistoryFilter
from apps.view_history.models import ViewHistory
from apps.view_history.serializers import ViewHistorySerializer
from apps.view_history.services import get_popular_listings


class ViewHistoryViewSet(viewsets.ReadOnlyModelViewSet):
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

    @extend_schema(responses=ListingSerializer(many=True))
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
            serializer = ListingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ListingSerializer(queryset, many=True)
        return Response(serializer.data)

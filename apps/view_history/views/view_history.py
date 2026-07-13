from django.db.models import Count
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.listings.models import Listing
from apps.listings.serializers import ListingSerializer
from apps.view_history.filters import ViewHistoryFilter
from apps.view_history.models import ViewHistory
from apps.view_history.serializers import ViewHistorySerializer


class ViewHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = ViewHistorySerializer
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
    @action(detail=False, methods=("get",), url_path="popular-listings")
    def popular_listings(self, request):
        queryset = (
            Listing.objects.active()
            .select_related("owner")
            .prefetch_related("images")
            .annotate(views_count=Count("view_history"))
            .filter(views_count__gt=0)
            .order_by("-views_count", "-created_at")
        )
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = ListingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ListingSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        view_history, created = ViewHistory.objects.update_or_create(
            user=request.user,
            listing=serializer.validated_data["listing"],
            defaults={},
        )
        response_serializer = self.get_serializer(view_history)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response(response_serializer.data, status=response_status)

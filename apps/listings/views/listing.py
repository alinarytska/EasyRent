from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework import viewsets

from apps.listings.filters import ListingFilter
from apps.listings.models import Listing
from apps.listings.permissions import ListingPermission
from apps.listings.serializers import ListingSerializer
from apps.search_history.services import record_listing_search
from apps.view_history.services import record_listing_view


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = (ListingPermission,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = ListingFilter
    search_fields = (
        "title",
        "description",
        "city",
        "district",
        "street",
    )
    ordering_fields = (
        "price_per_night",
        "rooms",
        "views_count",
        "created_at",
    )
    ordering = ("-created_at",)

    def get_queryset(self):
        return (
            Listing.objects.select_related("owner")
            .prefetch_related("images")
            .annotate(views_count=Count("view_history"))
            .all()
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        record_listing_search(
            user=request.user,
            query_params=request.query_params,
        )

        return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        record_listing_view(user=request.user, listing=instance)

        if hasattr(instance, "views_count"):
            instance.views_count = instance.view_history.count()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=("get",), url_path="my")
    def my_listings(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().by_owner(request.user),
        )
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=("get",), url_path="popular")
    def popular(self, request):
        queryset = self.get_queryset().order_by("-views_count", "-created_at")
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

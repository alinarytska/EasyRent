from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import viewsets

from apps.listings.filters import ListingFilter
from apps.listings.models import Listing
from apps.listings.serializers import ListingSerializer


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
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
        "created_at",
    )
    ordering = ("-created_at",)

    def get_queryset(self):
        return (
            Listing.objects.select_related("owner")
            .prefetch_related("images")
            .all()
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework import viewsets

from apps.listings.models import ListingImage
from apps.listings.serializers import ListingImageSerializer


class ListingImageViewSet(viewsets.ModelViewSet):
    serializer_class = ListingImageSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = (
        "listing",
        "is_primary",
    )
    ordering_fields = (
        "position",
        "uploaded_at",
    )
    ordering = (
        "-is_primary",
        "position",
        "id",
    )

    def get_queryset(self):
        return ListingImage.objects.select_related(
            "listing",
            "listing__owner",
        ).all()

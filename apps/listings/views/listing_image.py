from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter

from apps.listings.models import ListingImage
from apps.listings.permissions import ListingImagePermission
from apps.listings.serializers import ListingImageSerializer


class ListingImageViewSet(viewsets.ModelViewSet):
    serializer_class = ListingImageSerializer
    permission_classes = (ListingImagePermission,)
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
        queryset = ListingImage.objects.select_related(
            "listing",
            "listing__owner",
        ).all()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.is_staff:
            return queryset

        return queryset.filter(
            Q(listing__is_active=True) | Q(listing__owner=user),
        )

    def perform_create(self, serializer):
        listing = serializer.validated_data["listing"]

        if listing.owner_id != self.request.user.id:
            raise PermissionDenied(
                "You can manage images only for your own listings."
            )

        serializer.save()

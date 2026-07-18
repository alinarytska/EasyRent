from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter

from apps.listings.models import ListingImage
from apps.listings.permissions import ListingImagePermission
from apps.listings.serializers import ListingImageSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List listing images",
        description="Return images for active listings and for listings owned by the user.",
    ),
    retrieve=extend_schema(
        summary="Retrieve listing image",
        description="Return details for one listing image visible to the current user.",
    ),
    create=extend_schema(
        summary="Upload listing image",
        description="Upload an image for a listing owned by the authenticated landlord.",
    ),
    update=extend_schema(
        summary="Replace listing image",
        description="Replace image metadata or file for a listing owned by the user.",
    ),
    partial_update=extend_schema(
        summary="Update listing image",
        description="Partially update image metadata or file for a listing owned by the user.",
    ),
    destroy=extend_schema(
        summary="Delete listing image",
        description="Delete an image from a listing owned by the authenticated landlord.",
    ),
)
class ListingImageViewSet(viewsets.ModelViewSet):
    """API endpoints for uploading and managing listing images."""

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

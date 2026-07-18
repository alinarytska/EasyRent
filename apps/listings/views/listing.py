from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework import viewsets

from apps.common.mixins import ProtectedDestroyMixin
from apps.listings.filters import ListingFilter
from apps.listings.models import Listing
from apps.listings.permissions import ListingPermission
from apps.listings.serializers import ListingSerializer, PublicListingSerializer
from apps.reviews.serializers import ReviewSerializer
from apps.reviews.services import get_reviews_for_listing
from apps.search_history.services import record_listing_search
from apps.view_history.services import get_popular_listings, record_listing_view


@extend_schema_view(
    list=extend_schema(
        summary="List active listings",
        description=(
            "Return a paginated public catalog of active rental listings. "
            "Authenticated searches are saved to the user's search history."
        ),
    ),
    retrieve=extend_schema(
        summary="Retrieve listing details",
        description=(
            "Return details for one active listing. Authenticated views are "
            "saved to the user's view history."
        ),
    ),
    create=extend_schema(
        summary="Create listing",
        description="Create a new listing for the authenticated landlord.",
    ),
    update=extend_schema(
        summary="Replace listing",
        description="Replace an existing listing owned by the authenticated landlord.",
    ),
    partial_update=extend_schema(
        summary="Update listing",
        description="Partially update an existing listing owned by the authenticated landlord.",
    ),
    destroy=extend_schema(
        summary="Delete listing",
        description=(
            "Delete a listing only when it is safe to remove. Listings with "
            "bookings should be deactivated instead."
        ),
    ),
)
class ListingViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    """API endpoints for listing CRUD, search, filtering and popularity."""

    serializer_class = ListingSerializer
    permission_classes = (ListingPermission,)
    protected_destroy_error_message = (
        "Listing with bookings cannot be deleted. Deactivate it instead."
    )
    throttle_scope = "listings"
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

    def get_serializer_class(self):
        if getattr(self, "action", None) in ("list", "retrieve", "popular"):
            return PublicListingSerializer

        return ListingSerializer

    def get_queryset(self):
        queryset = (
            Listing.objects.select_related("owner")
            .prefetch_related("images")
            .annotate(views_count=Count("view_history"))
            .all()
        )
        user = self.request.user
        action = getattr(self, "action", None)

        if action == "my_listings":
            return queryset

        if not user.is_authenticated:
            return queryset.active()

        if action in (
            "retrieve",
            "update",
            "partial_update",
            "destroy",
            "reviews",
        ):
            return queryset.filter(
                Q(is_active=True) | Q(owner=user),
            )

        return queryset.active()

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

    @extend_schema(
        summary="List listing reviews",
        description="Return all reviews connected to completed bookings for this listing.",
        responses=ReviewSerializer(many=True),
    )
    @action(detail=True, methods=("get",), url_path="reviews")
    def reviews(self, request, pk=None):
        listing = self.get_object()
        queryset = get_reviews_for_listing(listing)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ReviewSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="List my listings",
        description="Return listings owned by the authenticated landlord, including inactive ones.",
    )
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

    @extend_schema(
        summary="List popular listings",
        description="Return active listings ordered by recorded view count.",
    )
    @action(
        detail=False,
        methods=("get",),
        url_path="popular",
        throttle_scope="popular",
    )
    def popular(self, request):
        queryset = get_popular_listings(active_only=True)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

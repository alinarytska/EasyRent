from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.reviews.filters import ReviewFilter
from apps.reviews.models import Review
from apps.reviews.permissions import ReviewPermission
from apps.reviews.serializers import ReviewSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List reviews",
        description="Return reviews visible to the current renter or listing owner.",
    ),
    retrieve=extend_schema(
        summary="Retrieve review",
        description="Return one review visible to the current user.",
    ),
    create=extend_schema(
        summary="Create review",
        description="Create a review for the current renter's completed booking.",
    ),
    update=extend_schema(
        summary="Replace review",
        description="Replace a review written by the authenticated renter.",
    ),
    partial_update=extend_schema(
        summary="Update review",
        description="Partially update a review written by the authenticated renter.",
    ),
    destroy=extend_schema(
        summary="Delete review",
        description="Delete a review written by the authenticated renter.",
    ),
)
class ReviewViewSet(viewsets.ModelViewSet):
    """API endpoints for creating and managing booking reviews."""

    serializer_class = ReviewSerializer
    permission_classes = (ReviewPermission,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = ReviewFilter
    ordering_fields = (
        "rating",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = Review.objects.select_related(
            "booking",
            "booking__listing",
            "booking__listing__owner",
            "booking__renter",
        )
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        return queryset.filter(
            Q(booking__renter=user) | Q(booking__listing__owner=user),
        ).distinct()

    @extend_schema(
        summary="List my reviews",
        description="Return reviews written by the authenticated renter.",
    )
    @action(detail=False, methods=("get",), url_path="my")
    def my_reviews(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(booking__renter=request.user),
        )
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

from django.db.models import Q
from rest_framework import viewsets

from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

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

        if user.is_staff:
            return queryset

        return queryset.filter(
            Q(booking__renter=user) | Q(booking__listing__owner=user),
        ).distinct()

from rest_framework import viewsets

from apps.listings.models import ListingImage
from apps.listings.serializers import ListingImageSerializer


class ListingImageViewSet(viewsets.ModelViewSet):
    serializer_class = ListingImageSerializer

    def get_queryset(self):
        return ListingImage.objects.select_related("listing").all()

from rest_framework.routers import DefaultRouter

from apps.listings.views import ListingImageViewSet, ListingViewSet


app_name = "listings"

router = DefaultRouter()
router.register("images", ListingImageViewSet, basename="listing-image")
router.register("", ListingViewSet, basename="listing")

urlpatterns = router.urls

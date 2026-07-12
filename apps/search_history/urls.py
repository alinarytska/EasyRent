from rest_framework.routers import DefaultRouter

from apps.search_history.views import SearchHistoryViewSet


app_name = "search_history"

router = DefaultRouter()
router.register("", SearchHistoryViewSet, basename="search-history")

urlpatterns = router.urls

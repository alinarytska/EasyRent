from rest_framework.routers import DefaultRouter

from apps.view_history.views import ViewHistoryViewSet


app_name = "view_history"

router = DefaultRouter()
router.register("", ViewHistoryViewSet, basename="view-history")

urlpatterns = router.urls

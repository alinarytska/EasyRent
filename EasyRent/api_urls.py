from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.users.views import (
    JWTLogoutView,
    JWTTokenObtainPairView,
    JWTTokenRefreshView,
)


urlpatterns = [
    path(
        "",
        RedirectView.as_view(url="docs/", permanent=False),
        name="api-v1-root-redirect",
    ),
    path(
        "auth/token/",
        JWTTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "auth/token/refresh/",
        JWTTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("auth/logout/", JWTLogoutView.as_view(), name="token_logout"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("users/", include("apps.users.urls")),
    path("listings/", include("apps.listings.urls")),
    path("bookings/", include("apps.bookings.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("search-history/", include("apps.search_history.urls")),
    path("view-history/", include("apps.view_history.urls")),
]

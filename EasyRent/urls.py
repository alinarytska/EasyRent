from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.users.views import (
    JWTLogoutView,
    JWTTokenObtainPairView,
    JWTTokenRefreshView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'api/auth/token/',
        JWTTokenObtainPairView.as_view(),
        name='token_obtain_pair',
    ),
    path(
        'api/auth/token/refresh/',
        JWTTokenRefreshView.as_view(),
        name='token_refresh',
    ),
    path('api/auth/logout/', JWTLogoutView.as_view(), name='token_logout'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path('api/users/', include('apps.users.urls')),
    path('api/listings/', include('apps.listings.urls')),
    path('api/bookings/', include('apps.bookings.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/search-history/', include('apps.search_history.urls')),
    path('api/view-history/', include('apps.view_history.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

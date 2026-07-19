from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path(
        "",
        RedirectView.as_view(url="/api/v1/docs/", permanent=False),
        name="api-root-redirect",
    ),
    path('admin/', admin.site.urls),
    path('api/v1/', include('EasyRent.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

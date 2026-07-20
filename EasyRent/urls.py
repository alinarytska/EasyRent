from django.contrib import admin
from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve
from django.views.generic import RedirectView


def serve_media_file(request, path):
    """Serve uploaded media files when local media serving is enabled."""

    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path(
        "",
        RedirectView.as_view(url="/api/v1/docs/", permanent=False),
        name="api-root-redirect",
    ),
    path('admin/', admin.site.urls),
    path('api/v1/', include('EasyRent.api_urls')),
]

if settings.DEBUG or settings.SERVE_MEDIA_FILES:
    urlpatterns += [
        re_path(
            rf"^{settings.MEDIA_URL.lstrip('/')}(?P<path>.*)$",
            serve_media_file,
            name="media-file",
        ),
    ]

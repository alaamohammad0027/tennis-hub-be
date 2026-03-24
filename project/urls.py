# urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("apis/auth/", include("accounts.urls")),
    path("apis/management/", include("management.urls")),
    path("apis/feed/", include("feed.urls")),
    path("apis/tennis/", include("tennis.urls")),
]

# API Documentation URLs
urlpatterns += [
    path("apis/schema/", SpectacularAPIView.as_view(), name="api_schema"),
    path(
        "apis/swagger/",
        SpectacularSwaggerView.as_view(url_name="api_schema"),
        name="api_schema_swagger_ui",
    ),
    path(
        "apis/docs/",
        SpectacularRedocView.as_view(url_name="api_schema"),
        name="api_schema_redoc_ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

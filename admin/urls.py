"""
URL configuration for Exo Admin.

Routes for admin interface, custom pages, and API endpoints.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from admin.apps.logs.views import errors_list

urlpatterns = [
    # Custom pages (before admin to override)
    path("", include("admin.apps.core.urls")),
    path("memories/", include("admin.apps.memories.urls")),
    path("ingest/", include("admin.apps.ingest.urls")),
    path("query/", include("admin.apps.query.urls")),
    path("commitments/", include("admin.apps.commitments.urls")),
    path("logs/", include("admin.apps.logs.urls")),
    path("integrations/", include("admin.apps.integrations.urls")),
    path("errors/", errors_list, name="errors"),
    
    # Django admin
    path("admin/", admin.site.urls),
]

# Serve static/media in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

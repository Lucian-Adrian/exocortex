"""
Memories URL patterns.
"""

from django.urls import path
from admin.apps.memories import views

app_name = "memories"

urlpatterns = [
    path("", views.memory_list, name="list"),
    path("<uuid:memory_id>/", views.memory_detail, name="detail"),
    path("<uuid:memory_id>/delete/", views.memory_delete, name="delete"),
    path("export/", views.memory_export, name="export"),
    path("api/search/", views.api_search, name="api_search"),
]

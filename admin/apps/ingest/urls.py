"""
Ingest URL patterns.
"""

from django.urls import path
from admin.apps.ingest import views

app_name = "ingest"

urlpatterns = [
    path("", views.ingest_page, name="page"),
    path("submit/", views.ingest_submit, name="submit"),
    path("text/", views.ingest_text, name="text"),
    path("file/", views.ingest_file, name="file"),
    path("api/", views.api_ingest, name="api"),
]

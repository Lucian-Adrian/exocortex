"""
Query URL patterns.
"""

from django.urls import path
from admin.apps.query import views

app_name = "query"

urlpatterns = [
    path("", views.query_page, name="page"),
    path("run/", views.run_query, name="run"),
    path("api/", views.api_query, name="api"),
    path("history/", views.query_history, name="history"),
]

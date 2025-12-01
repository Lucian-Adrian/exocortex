"""
Core URL patterns.
"""

from django.urls import path
from admin.apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", views.home, name="home"),
    path("analytics/", views.analytics, name="analytics"),
    path("settings/", views.settings_view, name="settings"),
    path("api/stats/", views.api_stats, name="api_stats"),
]

"""
Commitments URL patterns.
"""

from django.urls import path
from admin.apps.commitments import views

app_name = "commitments"

urlpatterns = [
    path("", views.commitment_list, name="list"),
    path("<uuid:commitment_id>/", views.commitment_detail, name="detail"),
    path("<uuid:commitment_id>/status/", views.update_status, name="update_status"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("api/", views.api_commitments, name="api"),
]

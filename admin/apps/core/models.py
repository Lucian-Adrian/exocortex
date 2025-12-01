"""
Core models for admin metadata.
"""

from django.db import models
from django.contrib.auth.models import User


class AdminSettings(models.Model):
    """Global admin settings stored in local DB."""
    
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Setting"
        verbose_name_plural = "Settings"
        ordering = ["key"]

    def __str__(self):
        return self.key


class ActivityLog(models.Model):
    """Track user activity in the admin."""
    
    ACTION_CHOICES = [
        ("ingest", "Ingested Content"),
        ("query", "Ran Query"),
        ("view", "Viewed Memory"),
        ("edit", "Edited Memory"),
        ("delete", "Deleted Memory"),
        ("export", "Exported Data"),
        ("setting", "Changed Setting"),
    ]
    
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"

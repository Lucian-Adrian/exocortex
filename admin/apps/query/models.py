"""
Query models for storing query history.
"""

from django.db import models
from django.contrib.auth.models import User


class QueryHistory(models.Model):
    """Store query history for analytics and quick re-run."""
    
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    question = models.TextField()
    answer = models.TextField()
    confidence = models.FloatField(default=0.0)
    sources = models.JSONField(default=list)
    commitments = models.JSONField(default=list)
    parameters = models.JSONField(default=dict)  # top_k, threshold, etc.
    execution_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Query History"
        verbose_name_plural = "Query History"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.question[:50]}... ({self.created_at})"

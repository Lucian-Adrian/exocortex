"""
Core utilities.
"""

from django.conf import settings


def environment_callback(request):
    """Return environment name for Unfold header."""
    if settings.DEBUG:
        return ["Development", "warning"]
    return ["Production", "success"]


def get_client_ip(request):
    """Get client IP from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

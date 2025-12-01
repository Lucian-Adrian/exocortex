"""
Context processors for templates.
"""

from django.conf import settings


def exo_context(request):
    """Add Exo-specific context to all templates."""
    return {
        "exo_version": "0.1.0",
        "debug": settings.DEBUG,
        "supabase_url": settings.SUPABASE_URL,
    }

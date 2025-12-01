"""
Commitments utilities.
"""

from admin.apps.core.services import get_supabase_client


def open_commitments_badge(request):
    """Return open commitments count for sidebar badge."""
    try:
        client = get_supabase_client()
        response = client.table("commitments").select("id", count="exact").eq(
            "status", "open"
        ).execute()
        count = response.count or 0
        if count == 0:
            return None  # Hide badge if no open commitments
        return str(count)
    except Exception:
        return "?"

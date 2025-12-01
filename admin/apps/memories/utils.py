"""
Memories utilities.
"""

from admin.apps.core.services import get_supabase_client


def memory_count_badge(request):
    """Return memory count for sidebar badge."""
    try:
        client = get_supabase_client()
        response = client.table("memories").select("id", count="exact").execute()
        count = response.count or 0
        return str(count) if count < 1000 else f"{count // 1000}k+"
    except Exception:
        return "?"

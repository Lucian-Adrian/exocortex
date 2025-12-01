"""
Core services - Supabase integration, stats with caching.

Optimized for performance:
- Parallel database queries using concurrent.futures
- Time-based caching for stats
- Connection pooling via singleton client
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from threading import Lock
from typing import Any

from django.conf import settings
from supabase import create_client, Client


# ============================================================================
# CLIENT SINGLETON
# ============================================================================

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Get cached Supabase client (singleton)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


# ============================================================================
# STATS CACHING
# ============================================================================

_stats_cache: dict[str, Any] = {}
_stats_cache_time: float = 0
_stats_cache_lock = Lock()
STATS_CACHE_TTL = 30  # seconds


def _fetch_total_memories(client: Client) -> tuple[str, int]:
    """Fetch total memory count."""
    resp = client.table("memories").select("id", count="exact").execute()
    return ("total_memories", resp.count or 0)


def _fetch_memories_today(client: Client, today_start: str) -> tuple[str, int]:
    """Fetch memories created today."""
    resp = client.table("memories").select("id", count="exact").gte("created_at", today_start).execute()
    return ("memories_today", resp.count or 0)


def _fetch_open_commitments(client: Client) -> tuple[str, int]:
    """Fetch open commitment count."""
    resp = client.table("commitments").select("id", count="exact").eq("status", "open").execute()
    return ("open_commitments", resp.count or 0)


def _fetch_overdue_commitments(client: Client, today: str) -> tuple[str, int]:
    """Fetch overdue commitment count."""
    resp = client.table("commitments").select("id", count="exact").eq("status", "open").lt("due_date", today).execute()
    return ("overdue_commitments", resp.count or 0)


def _fetch_errors_24h(client: Client, yesterday: str) -> tuple[str, int]:
    """Fetch error count in last 24h."""
    resp = client.table("_errors").select("id", count="exact").gte("created_at", yesterday).execute()
    return ("errors_24h", resp.count or 0)


def _fetch_recent_memories(client: Client) -> tuple[str, list]:
    """Fetch recent memories for activity feed."""
    resp = client.table("memories").select("id, summary, source_type, created_at").order("created_at", desc=True).limit(5).execute()
    return ("recent_memories", resp.data or [])


def _fetch_source_distribution(client: Client) -> tuple[str, dict]:
    """Fetch source type distribution."""
    resp = client.table("memories").select("source_type").execute()
    counts: dict[str, int] = {}
    for item in resp.data or []:
        st = item.get("source_type", "unknown")
        counts[st] = counts.get(st, 0) + 1
    return ("source_distribution", counts)


def get_stats_sync() -> dict:
    """
    Get dashboard statistics with caching and parallel fetching.
    
    - Returns cached stats if within TTL
    - Fetches all stats in parallel using ThreadPoolExecutor
    - Much faster than sequential async calls
    """
    global _stats_cache, _stats_cache_time
    
    # Check cache
    with _stats_cache_lock:
        if _stats_cache and (time.time() - _stats_cache_time) < STATS_CACHE_TTL:
            return _stats_cache.copy()
    
    client = get_supabase_client()
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today = now.date().isoformat()
    yesterday = (now - timedelta(days=1)).isoformat()
    
    stats: dict[str, Any] = {}
    
    try:
        # Run all queries in parallel
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = [
                executor.submit(_fetch_total_memories, client),
                executor.submit(_fetch_memories_today, client, today_start),
                executor.submit(_fetch_open_commitments, client),
                executor.submit(_fetch_overdue_commitments, client, today),
                executor.submit(_fetch_errors_24h, client, yesterday),
                executor.submit(_fetch_recent_memories, client),
                executor.submit(_fetch_source_distribution, client),
            ]
            
            for future in as_completed(futures):
                try:
                    key, value = future.result()
                    stats[key] = value
                except Exception:
                    pass  # Individual query failed, continue
        
        # Local DB query (fast)
        from admin.apps.core.models import ActivityLog
        stats["queries_today"] = ActivityLog.objects.filter(
            action="query",
            created_at__gte=now.replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
    except Exception as e:
        stats["error"] = str(e)
    
    # Update cache
    with _stats_cache_lock:
        _stats_cache = stats
        _stats_cache_time = time.time()
    
    return stats


def invalidate_stats_cache():
    """Invalidate the stats cache (call after data changes)."""
    global _stats_cache, _stats_cache_time
    with _stats_cache_lock:
        _stats_cache = {}
        _stats_cache_time = 0


# Async wrapper for backward compatibility
async def get_stats() -> dict:
    """Get dashboard statistics (async wrapper)."""
    return get_stats_sync()


# ============================================================================
# DATA ACCESS - SYNCHRONOUS (faster than async for simple queries)
# ============================================================================

def get_memory_by_id_sync(memory_id: str) -> dict | None:
    """Get a single memory by ID."""
    client = get_supabase_client()
    response = client.table("memories").select("*").eq("id", memory_id).single().execute()
    return response.data


async def get_memory_by_id(memory_id: str) -> dict | None:
    """Get a single memory by ID (async wrapper)."""
    return get_memory_by_id_sync(memory_id)


def search_memories_sync(query: str = "", source_type: str | None = None, limit: int = 50) -> list:
    """Search memories with optional filters."""
    client = get_supabase_client()
    q = client.table("memories").select("*")
    if source_type:
        q = q.eq("source_type", source_type)
    q = q.order("created_at", desc=True).limit(limit)
    return q.execute().data or []


async def search_memories(query: str = "", source_type: str | None = None, limit: int = 50) -> list:
    """Search memories (async wrapper)."""
    return search_memories_sync(query, source_type, limit)


def get_commitments_sync(status: str | None = None, limit: int = 50) -> list:
    """Get commitments with optional status filter."""
    client = get_supabase_client()
    q = client.table("commitments").select("*")
    if status:
        q = q.eq("status", status)
    q = q.order("due_date", nulls_first=False).limit(limit)
    return q.execute().data or []


async def get_commitments(status: str | None = None, limit: int = 50) -> list:
    """Get commitments (async wrapper)."""
    return get_commitments_sync(status, limit)


def get_errors_sync(limit: int = 100) -> list:
    """Get recent errors."""
    client = get_supabase_client()
    return client.table("_errors").select("*").order("created_at", desc=True).limit(limit).execute().data or []


async def get_errors(limit: int = 100) -> list:
    """Get recent errors (async wrapper)."""
    return get_errors_sync(limit)


# ============================================================================
# OPTIMIZED LIST QUERIES
# ============================================================================

def get_memories_list(
    source_type: str = "",
    ordering: str = "-created_at",
    has_commitments: bool = False,
    search: str = "",
    limit: int = 100,
) -> tuple[list, list]:
    """
    Get memories list with filters and source types in parallel.
    Returns: (memories, source_types)
    """
    client = get_supabase_client()
    
    def fetch_memories():
        q = client.table("memories").select(
            "id, content, summary, source_type, source_file, intents, commitments, created_at"
        )
        if source_type:
            q = q.eq("source_type", source_type)
        if has_commitments:
            q = q.neq("commitments", [])
        if ordering.startswith("-"):
            q = q.order(ordering[1:], desc=True)
        else:
            q = q.order(ordering)
        return q.limit(limit).execute().data or []
    
    def fetch_source_types():
        resp = client.table("memories").select("source_type").execute()
        return list(set(item.get("source_type") for item in resp.data or [] if item.get("source_type")))
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        mem_future = executor.submit(fetch_memories)
        src_future = executor.submit(fetch_source_types)
        memories = mem_future.result()
        source_types = src_future.result()
    
    if search:
        search_lower = search.lower()
        memories = [m for m in memories if search_lower in m.get("content", "").lower() or search_lower in m.get("summary", "").lower()]
    
    return memories, sorted(source_types)

"""
Database query functions.

Implements the data access layer using Supabase client.
All functions take a client instance as an argument (Dependency Injection).
"""

from datetime import datetime
from typing import Any

from supabase import Client

from exo.schemas.memory import Memory


async def insert_memory(client: Client, memory: Memory) -> str:
    """
    Insert a memory record into the database.

    Uses content_hash for idempotency (ON CONFLICT DO UPDATE).
    Returns the UUID of the inserted/updated record.
    """
    # Convert Pydantic model to dict, excluding None values where appropriate
    # Note: embedding is required for vector search
    data = memory.model_dump(exclude={"id", "created_at", "updated_at"}, mode="json")

    # Supabase-py doesn't support ON CONFLICT DO UPDATE easily in one call
    # without using upsert.
    # upsert(data, on_conflict="content_hash")
    response = client.table("memories").upsert(data, on_conflict="content_hash").execute()

    if not response.data:
        raise RuntimeError(f"Failed to insert memory: {response}")

    return response.data[0]["id"]


async def search_semantic(
    client: Client,
    embedding: list[float],
    match_threshold: float = 0.7,
    match_count: int = 10,
    filter_source_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Perform semantic search using vector similarity.

    Calls the `match_memories` RPC function in Postgres.
    """
    params = {
        "query_embedding": embedding,
        "match_threshold": match_threshold,
        "match_count": match_count,
        "filter_source_type": filter_source_type,
    }

    response = client.rpc("match_memories", params).execute()
    return response.data


async def get_commitments(
    client: Client,
    status: str | None = None,
    due_before: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Get commitments with optional filtering.
    """
    query = client.table("commitments").select("*")

    if status:
        query = query.eq("status", status)

    if due_before:
        query = query.lte("due_date", due_before.isoformat())

    # Order by due_date ascending (nulls last), then created_at desc
    query = query.order("due_date", nulls_first=False).order(
        "created_at", desc=True
    )

    response = query.execute()
    return response.data


async def log_error(client: Client, error_data: dict[str, Any]) -> None:
    """
    Log an error to the _errors table.
    """
    # Ensure we match the schema
    payload = {
        "error_code": error_data.get("code", "UNKNOWN"),
        "message": error_data.get("message", "Unknown error"),
        "details": error_data.get("details", {}),
        "source": error_data.get("source", "exo"),
    }
    client.table("_errors").insert(payload).execute()

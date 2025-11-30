"""
Ingest endpoint.

Handles content ingestion via REST API.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from exo.schemas.content import RawContent
from exo.schemas.errors import ExoError
from exo.schemas.memory import Memory

router = APIRouter()


@router.post("/ingest", response_model=dict)
async def ingest_content(content: RawContent, request: Request) -> dict[str, Any]:
    """
    Ingest content into memory.

    Args:
        content: Raw content to ingest
        request: FastAPI request object

    Returns:
        Ingested memory or error
    """
    orchestrator = request.app.state.orchestrator

    result = await orchestrator.ingest(content)

    if isinstance(result, ExoError):
        raise HTTPException(
            status_code=400,
            detail={
                "code": result.code.value,
                "message": result.message,
                "details": result.details,
            },
        )

    # Convert Memory to response dict
    return {
        "success": True,
        "memory": _memory_to_dict(result),
    }


def _memory_to_dict(memory: Memory) -> dict[str, Any]:
    """Convert Memory to dictionary for JSON response."""
    return {
        "id": str(memory.id) if memory.id else None,
        "content": memory.content,
        "summary": memory.summary,
        "intents": memory.intents,
        "entities": memory.entities,
        "commitments": memory.commitments,
        "source_type": memory.source_type.value,
        "source_file": memory.source_file,
        "content_hash": memory.content_hash,
        "created_at": memory.created_at.isoformat() if memory.created_at else None,
    }

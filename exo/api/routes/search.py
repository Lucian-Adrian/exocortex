"""
Search endpoint.

Handles semantic search via REST API.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from exo.db.queries import search_semantic
from exo.schemas.errors import ExoError

router = APIRouter()


@router.get("/search")
async def search_memories(
    request: Request,
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results"),
    threshold: float = Query(default=0.7, ge=0.0, le=1.0, description="Similarity threshold"),
) -> dict[str, Any]:
    """
    Search memories by semantic similarity.

    Args:
        request: FastAPI request object
        q: Search query text
        limit: Maximum number of results
        threshold: Minimum similarity threshold

    Returns:
        List of matching memories
    """
    orchestrator = request.app.state.orchestrator

    # Get embedding for query
    if orchestrator._embedding_provider is None:
        raise HTTPException(status_code=500, detail="Embedding provider not available")

    try:
        embedding = await orchestrator._embedding_provider.embed(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    # Search database
    if orchestrator._client is None:
        raise HTTPException(status_code=500, detail="Database client not available")

    result = await search_semantic(
        client=orchestrator._client,
        embedding=embedding,
        limit=limit,
        threshold=threshold,
    )

    if isinstance(result, ExoError):
        raise HTTPException(
            status_code=400,
            detail={
                "code": result.code.value,
                "message": result.message,
            },
        )

    # Format results
    return {
        "success": True,
        "query": q,
        "count": len(result),
        "results": [
            {
                "id": str(r.get("id", "")),
                "summary": r.get("summary", ""),
                "similarity": r.get("similarity", 0.0),
                "topics": r.get("topics", []),
                "created_at": r.get("created_at"),
            }
            for r in result
        ],
    }

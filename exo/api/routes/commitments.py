"""
Commitments endpoint.

Handles commitment queries via REST API.
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from exo.db.queries import get_commitments
from exo.schemas.errors import ExoError

router = APIRouter()


@router.get("/commitments")
async def list_commitments(
    request: Request,
    status: str | None = Query(default=None, description="Filter by status (open, completed, cancelled)"),
    due_before: date | None = Query(default=None, description="Filter by due date (YYYY-MM-DD)"),
) -> dict[str, Any]:
    """
    List commitments with optional filters.

    Args:
        request: FastAPI request object
        status: Filter by commitment status
        due_before: Filter by due date

    Returns:
        List of commitments
    """
    orchestrator = request.app.state.orchestrator

    if orchestrator._client is None:
        raise HTTPException(status_code=500, detail="Database client not available")

    result = await get_commitments(
        client=orchestrator._client,
        status=status,
        due_before=due_before,
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
        "count": len(result),
        "commitments": [
            {
                "id": str(r.get("id", "")),
                "from_party": r.get("from_party", ""),
                "to_party": r.get("to_party", ""),
                "description": r.get("description", ""),
                "status": r.get("status", "open"),
                "due_date": r.get("due_date"),
                "memory_id": str(r.get("memory_id", "")) if r.get("memory_id") else None,
                "created_at": r.get("created_at"),
            }
            for r in result
        ],
    }

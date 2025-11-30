"""
Query endpoint.

Handles RAG queries via REST API.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from exo.schemas.errors import ExoError
from exo.schemas.query import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/query", response_model=dict)
async def query_memory(request_body: QueryRequest, request: Request) -> dict[str, Any]:
    """
    Query memory with a question.

    Args:
        request_body: Query request with question and parameters
        request: FastAPI request object

    Returns:
        Query response with answer and sources
    """
    orchestrator = request.app.state.orchestrator

    result = await orchestrator.query(request_body)

    if isinstance(result, ExoError):
        raise HTTPException(
            status_code=400,
            detail={
                "code": result.code.value,
                "message": result.message,
                "details": result.details,
            },
        )

    # Convert QueryResponse to response dict
    return {
        "success": True,
        "answer": result.answer,
        "sources": [
            {
                "memory_id": s.memory_id,
                "content_preview": s.content_preview,
                "similarity": s.similarity,
                "source_file": s.source_file,
            }
            for s in result.sources
        ],
        "commitments": result.commitments,
        "confidence": result.confidence,
    }

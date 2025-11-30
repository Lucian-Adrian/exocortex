"""
Webhook endpoints for n8n compatibility.

Provides simplified webhook endpoints for automation platforms.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from exo.schemas.content import RawContent, SourceType
from exo.schemas.errors import ExoError
from exo.schemas.query import QueryRequest

router = APIRouter()


class WebhookIngestRequest(BaseModel):
    """Simplified ingest request for webhooks."""

    text: str
    source_type: str = "markdown"
    metadata: dict[str, Any] | None = None


class WebhookQueryRequest(BaseModel):
    """Simplified query request for webhooks."""

    question: str
    top_k: int = 5
    threshold: float = 0.7


@router.post("/ingest")
async def webhook_ingest(body: WebhookIngestRequest, request: Request) -> dict[str, Any]:
    """
    Webhook endpoint for content ingestion.

    n8n compatible format with simplified request body.

    Args:
        body: Webhook ingest request
        request: FastAPI request object

    Returns:
        Ingested memory summary
    """
    orchestrator = request.app.state.orchestrator

    # Map source type string to enum
    source_type_map = {
        "audio": SourceType.AUDIO,
        "telegram": SourceType.TELEGRAM,
        "markdown": SourceType.MARKDOWN,
        "slack": SourceType.SLACK,
        "code": SourceType.CODE,
    }
    src_type = source_type_map.get(body.source_type.lower(), SourceType.MARKDOWN)

    # Create RawContent
    content = RawContent(
        text=body.text,
        source_type=src_type,
        metadata=body.metadata or {},
    )

    result = await orchestrator.ingest(content)

    if isinstance(result, ExoError):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": result.message,
            },
        )

    # Return simplified response for n8n
    return {
        "success": True,
        "id": str(result.id) if result.id else None,
        "summary": result.summary,
        "commitment_count": len(result.commitments),
        "entity_count": len(result.entities) if isinstance(result.entities, dict) else 0,
    }


@router.post("/query")
async def webhook_query(body: WebhookQueryRequest, request: Request) -> dict[str, Any]:
    """
    Webhook endpoint for queries.

    n8n compatible format with simplified request body.

    Args:
        body: Webhook query request
        request: FastAPI request object

    Returns:
        Query answer and sources
    """
    orchestrator = request.app.state.orchestrator

    # Create QueryRequest
    query_request = QueryRequest(
        question=body.question,
        top_k=body.top_k,
        similarity_threshold=body.threshold,
    )

    result = await orchestrator.query(query_request)

    if isinstance(result, ExoError):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": result.message,
            },
        )

    # Return simplified response for n8n
    return {
        "success": True,
        "answer": result.answer,
        "source_count": len(result.sources),
        "confidence": result.confidence,
    }

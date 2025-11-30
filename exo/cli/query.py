"""
Query command implementation.

Handles searching memory and generating answers.
"""

import asyncio
from typing import Any

from exo.pipeline import PipelineOrchestrator
from exo.schemas.errors import ExoError
from exo.schemas.query import QueryRequest


def run_query(
    question: str,
    top_k: int = 5,
    threshold: float = 0.7,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Run the query pipeline.

    Args:
        question: Question to ask
        top_k: Number of results to retrieve
        threshold: Similarity threshold
        verbose: Enable verbose output

    Returns:
        Dictionary with query result or error
    """
    request = QueryRequest(
        question=question,
        top_k=top_k,
        similarity_threshold=threshold,
    )

    if verbose:
        print(f"[DEBUG] Question: {question}")
        print(f"[DEBUG] Top K: {top_k}, Threshold: {threshold}")

    # Run the query pipeline
    result = asyncio.run(_async_query(request, verbose))

    return result


async def _async_query(request: QueryRequest, verbose: bool) -> dict[str, Any]:
    """Async query implementation."""
    orchestrator = PipelineOrchestrator()

    result = await orchestrator.query(request)

    if isinstance(result, ExoError):
        return {
            "success": False,
            "error": {
                "code": result.code.value,
                "message": result.message,
                "details": result.details,
            },
        }

    # Convert QueryResponse to dict
    return {
        "success": True,
        "answer": result.answer,
        "sources": [
            {
                "content_preview": s.content_preview,
                "similarity": s.similarity,
                "memory_id": s.memory_id,
            }
            for s in result.sources
        ],
        "commitments": result.commitments,
        "confidence": result.confidence,
    }

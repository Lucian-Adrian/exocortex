"""
Ingest command implementation.

Handles parsing content and storing in memory.
"""

import asyncio
import json
from typing import Any

from exo.pipeline import PipelineOrchestrator
from exo.schemas.content import RawContent, SourceType
from exo.schemas.errors import ExoError


def run_ingest(content: str, source_type: str, verbose: bool = False) -> dict[str, Any]:
    """
    Run the ingest pipeline.

    Args:
        content: Raw content to ingest (text or JSON)
        source_type: Type of source (audio, telegram, markdown)
        verbose: Enable verbose output

    Returns:
        Dictionary with ingest result or error
    """
    # Try to parse as JSON first (for structured input)
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            text = data.get("text", content)
            source_type = data.get("source_type", source_type)
        else:
            text = content
    except json.JSONDecodeError:
        text = content

    # Map string to SourceType enum
    source_type_map = {
        "audio": SourceType.AUDIO,
        "telegram": SourceType.TELEGRAM,
        "markdown": SourceType.MARKDOWN,
        "slack": SourceType.SLACK,
        "code": SourceType.CODE,
    }
    src_type = source_type_map.get(source_type.lower(), SourceType.MARKDOWN)

    # Create raw content
    raw_content = RawContent(text=text, source_type=src_type)

    if verbose:
        print(f"[DEBUG] Source type: {src_type}")
        print(f"[DEBUG] Content length: {len(text)} chars")

    # Run the pipeline
    result = asyncio.run(_async_ingest(raw_content, verbose))

    return result


async def _async_ingest(content: RawContent, verbose: bool) -> dict[str, Any]:
    """Async ingest implementation."""
    orchestrator = PipelineOrchestrator()

    result = await orchestrator.ingest(content)

    if isinstance(result, ExoError):
        return {
            "success": False,
            "error": {
                "code": result.code.value,
                "message": result.message,
                "details": result.details,
            },
        }

    # Convert Memory to dict
    return {
        "success": True,
        "memory": {
            "id": str(result.id) if result.id else None,
            "content": result.content,
            "summary": result.summary,
            "intents": result.intents,
            "entities": result.entities,
            "commitments": result.commitments,
            "source_type": result.source_type.value,
            "created_at": result.created_at.isoformat() if result.created_at else None,
        },
    }

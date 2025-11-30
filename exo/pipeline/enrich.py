"""
Enrich pipeline step.

Uses AI provider to extract intents, entities, and commitments.
"""

from exo.ai.base import AIProvider
from exo.schemas.content import ParsedContent
from exo.schemas.enriched import EnrichedContent
from exo.schemas.errors import ExoError, ErrorCode


async def enrich(
    content: ParsedContent,
    provider: AIProvider,
) -> EnrichedContent | ExoError:
    """
    Enrich parsed content with AI-extracted metadata.
    
    Calls the AI provider to extract:
    - Intents (decision, commitment, question, etc.)
    - Named entities (people, companies, dates)
    - Commitments (promises, deadlines)
    - Summary
    - Topics
    
    Args:
        content: Parsed content with chunks.
        provider: AI provider for enrichment (REQUIRED - injected from orchestrator).
        
    Returns:
        EnrichedContent with extracted metadata, or ExoError on failure.
    """
    try:
        # Concatenate chunks for enrichment
        full_text = "\n\n".join(content.chunks)
        
        if not full_text.strip():
            return ExoError(
                code=ErrorCode.ENRICH_ERROR,
                message="No content to enrich - chunks are empty",
                details={"chunk_count": len(content.chunks)},
                recoverable=False,
            )
        
        return await provider.enrich(full_text)
        
    except ConnectionError as e:
        return ExoError(
            code=ErrorCode.AI_UNAVAILABLE,
            message=f"AI provider connection failed: {e}",
            details={"error_type": "ConnectionError"},
            recoverable=True,
        )
    except TimeoutError as e:
        return ExoError(
            code=ErrorCode.AI_UNAVAILABLE,
            message=f"AI provider timeout: {e}",
            details={"error_type": "TimeoutError"},
            recoverable=True,
        )
    except Exception as e:
        return ExoError(
            code=ErrorCode.ENRICH_ERROR,
            message=f"Enrichment failed: {e}",
            details={"error_type": type(e).__name__},
            recoverable=True,
        )

"""
Embed pipeline step.

Creates vector embeddings and Memory objects.
"""

import hashlib

from exo.ai.base import EmbeddingProvider
from exo.schemas.content import SourceType
from exo.schemas.enriched import EnrichedContent
from exo.schemas.memory import Memory
from exo.schemas.errors import ExoError, ErrorCode


async def embed(
    content: EnrichedContent,
    provider: EmbeddingProvider,
    source_type: SourceType | str = SourceType.MARKDOWN,
    source_file: str | None = None,
    original_content: str | None = None,
) -> Memory | ExoError:
    """
    Create Memory object with vector embedding.
    
    Generates embedding vector for the enriched content summary
    and creates a Memory object ready for storage.
    
    Args:
        content: Enriched content with metadata.
        provider: Embedding provider (REQUIRED - injected from orchestrator).
        
    Returns:
        Memory with embedding vector, or ExoError on failure.
    """
    try:
        # Use summary for embedding (most semantically dense)
        text_to_embed = content.summary
        
        if not text_to_embed.strip():
            return ExoError(
                code=ErrorCode.EMBED_ERROR,
                message="No text to embed - summary is empty",
                details={},
                recoverable=False,
            )
        
        # Generate embedding
        embedding = await provider.embed(text_to_embed)
        
        if not embedding:
            return ExoError(
                code=ErrorCode.EMBED_ERROR,
                message="Embedding provider returned empty vector",
                details={},
                recoverable=True,
            )
        
        # Convert entities to serializable dict
        entities_dict = {}
        for entity in content.entities:
            entity_type = entity.type
            if entity_type not in entities_dict:
                entities_dict[entity_type] = []
            entities_dict[entity_type].append({
                "name": entity.name,
                "confidence": entity.confidence,
                "normalized": entity.normalized,
            })
        
        # Convert commitments to serializable list
        commitments_list = [
            {
                "from_party": c.from_party,
                "to_party": c.to_party,
                "description": c.description,
                "due_date": c.due_date.isoformat() if c.due_date else None,
                "status": c.status,
            }
            for c in content.commitments
        ]
        
        # Normalize source_type to SourceType enum
        if isinstance(source_type, str):
            try:
                src_type = SourceType(source_type)
            except ValueError:
                src_type = SourceType.MARKDOWN  # Default fallback
        else:
            src_type = source_type
        
        # Generate content hash for deduplication
        hash_content = original_content or content.summary
        content_hash = hashlib.sha256(hash_content.encode()).hexdigest()
        
        # Create Memory object
        memory = Memory(
            content=content.summary,
            intents=[intent.value for intent in content.intents],
            entities=entities_dict,
            commitments=commitments_list,
            summary=content.summary,
            embedding=embedding,
            source_type=src_type,
            source_file=source_file,
            content_hash=content_hash,
        )
        
        return memory
        
    except ConnectionError as e:
        return ExoError(
            code=ErrorCode.AI_UNAVAILABLE,
            message=f"Embedding provider connection failed: {e}",
            details={"error_type": "ConnectionError"},
            recoverable=True,
        )
    except TimeoutError as e:
        return ExoError(
            code=ErrorCode.AI_UNAVAILABLE,
            message=f"Embedding provider timeout: {e}",
            details={"error_type": "TimeoutError"},
            recoverable=True,
        )
    except Exception as e:
        return ExoError(
            code=ErrorCode.EMBED_ERROR,
            message=f"Embedding failed: {e}",
            details={"error_type": type(e).__name__},
            recoverable=True,
        )

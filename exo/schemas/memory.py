"""
Memory schema for stored knowledge.

A Memory is the final product of the ingest pipeline:
- Original content + enrichment + embedding
- Ready for semantic search and RAG queries
"""

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field

from exo.schemas.content import SourceType


class Memory(BaseModel):
    """
    A stored memory with embedding for semantic search.

    This is the core data structure stored in the database.
    It combines:
    - Original content (text)
    - LLM enrichment (intents, entities, commitments)
    - Vector embedding (for similarity search)
    - Provenance (source info)
    """

    # Identity
    id: UUID | None = Field(
        default=None,
        description="Database-assigned UUID (None before insert)",
    )

    # Content
    content: str = Field(..., min_length=1, description="Full text content")
    summary: str = Field(..., min_length=1, description="LLM-generated summary")

    # Enrichment
    intents: list[str] = Field(
        default_factory=list,
        description="Intent classification tags",
    )
    entities: dict = Field(
        default_factory=dict,
        description="Extracted entities grouped by type",
    )
    commitments: list[dict] = Field(
        default_factory=list,
        description="Extracted commitments as dicts",
    )

    # Embedding
    embedding: list[float] | None = Field(
        default=None,
        description="768-dim vector embedding (text-embedding-004)",
    )

    # Provenance
    source_type: SourceType = Field(..., description="Original source type")
    source_file: str | None = Field(
        default=None,
        description="Original file path or identifier",
    )
    content_hash: str | None = Field(
        default=None,
        description="SHA-256 hash for deduplication",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this memory was created",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last update timestamp",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "content": "Meeting with John. We agreed on $99/month.",
                    "summary": "Pricing decision: $99/month with John.",
                    "intents": ["decision", "commitment"],
                    "entities": {"people": ["John"], "amounts": ["$99/month"]},
                    "commitments": [
                        {
                            "from_party": "me",
                            "to_party": "John",
                            "description": "send contract",
                        }
                    ],
                    "source_type": "audio",
                    "source_file": "meeting_2024-11-30.json",
                }
            ]
        }
    }

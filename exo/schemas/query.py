"""
Query schemas for RAG search and response.

These models define the interface for querying the memory system:
- QueryRequest: What to search for
- QueryResponse: Structured answer with sources
"""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """
    Request for querying the memory system.

    Supports semantic search with filtering.
    """

    question: str = Field(
        ...,
        min_length=1,
        description="Natural language question to answer",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of sources to retrieve",
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for results",
    )
    filters: dict = Field(
        default_factory=dict,
        description="Optional filters (source_type, date_range, intents)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What did I promise John?",
                    "top_k": 5,
                    "similarity_threshold": 0.7,
                    "filters": {"source_type": "audio"},
                }
            ]
        }
    }


class Source(BaseModel):
    """
    A source document used to answer a query.

    Links the answer back to specific memories.
    """

    memory_id: str = Field(..., description="UUID of the source memory")
    content_preview: str = Field(
        ...,
        max_length=500,
        description="Preview snippet of the content",
    )
    similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score to the query",
    )
    source_file: str | None = Field(
        default=None,
        description="Original source file for attribution",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "memory_id": "550e8400-e29b-41d4-a716-446655440000",
                    "content_preview": "Meeting with John. We agreed on $99/month...",
                    "similarity": 0.92,
                    "source_file": "meeting_2024-11-30.json",
                }
            ]
        }
    }


class QueryResponse(BaseModel):
    """
    Response from a RAG query.

    Contains:
    - Generated answer
    - Source attribution
    - Related commitments
    - Confidence score
    """

    answer: str = Field(..., min_length=1, description="Generated answer to the question")
    sources: list[Source] = Field(
        default_factory=list,
        description="Sources used to generate the answer",
    )
    commitments: list[dict] = Field(
        default_factory=list,
        description="Related commitments found in sources",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the answer (based on source quality)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": "You promised John to send the contract by Monday.",
                    "sources": [
                        {
                            "memory_id": "550e8400...",
                            "content_preview": "Meeting with John...",
                            "similarity": 0.92,
                        }
                    ],
                    "commitments": [
                        {
                            "to": "John",
                            "what": "send contract",
                            "due": "2024-12-02",
                        }
                    ],
                    "confidence": 0.91,
                }
            ]
        }
    }

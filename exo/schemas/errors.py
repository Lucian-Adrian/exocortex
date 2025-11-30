"""
Error schemas for pipeline error handling.

Follows the pattern: Return ExoError instead of raising exceptions.
This enables:
- Pattern matching on results
- Graceful degradation
- Structured error logging
"""

from enum import Enum

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """
    Error codes for pipeline failures.

    Each code maps to a specific failure mode:
    - PARSE_ERROR: Failed to parse input content
    - ENRICH_ERROR: LLM enrichment failed
    - EMBED_ERROR: Embedding generation failed
    - STORE_ERROR: Database storage failed
    - QUERY_ERROR: RAG query failed
    - VALIDATION_ERROR: Input validation failed
    - AI_UNAVAILABLE: AI provider unavailable
    """

    PARSE_ERROR = "PARSE_ERROR"
    ENRICH_ERROR = "ENRICH_ERROR"
    EMBED_ERROR = "EMBED_ERROR"
    STORE_ERROR = "STORE_ERROR"
    QUERY_ERROR = "QUERY_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AI_UNAVAILABLE = "AI_UNAVAILABLE"


class ExoError(BaseModel):
    """
    Structured error for pipeline failures.

    Used as return type instead of raising exceptions:

    ```python
    match await ingest(content):
        case Memory() as m:
            return {"status": "ok", "id": m.id}
        case ExoError() as e:
            await log_error(client, e.model_dump())
            return {"status": "error", "code": e.code}
    ```
    """

    code: ErrorCode = Field(..., description="Error code for categorization")
    message: str = Field(..., min_length=1, description="Human-readable error message")
    details: dict = Field(
        default_factory=dict,
        description="Additional context (input, stack trace, etc.)",
    )
    recoverable: bool = Field(
        default=True,
        description="Whether the operation can be retried",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "ENRICH_ERROR",
                    "message": "Gemini API returned invalid response",
                    "details": {"model": "gemini-2.5-flash-lite", "status_code": 500},
                    "recoverable": True,
                }
            ]
        }
    }

    def __str__(self) -> str:
        """Human-readable error representation."""
        return f"[{self.code.value}] {self.message}"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"ExoError(code={self.code!r}, message={self.message!r}, recoverable={self.recoverable})"

"""
Content schemas for raw and parsed content.

These models represent content at different stages of the pipeline:
- RawContent: Input from any source (audio, chat, markdown)
- ParsedContent: Structured content ready for enrichment
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Supported content source types."""

    AUDIO = "audio"
    TELEGRAM = "telegram"
    SLACK = "slack"
    MARKDOWN = "markdown"
    CODE = "code"


class RawContent(BaseModel):
    """
    Raw content from any input source.

    This is the entry point to the pipeline. Content can come from:
    - Audio transcriptions (Audio Toolkit, Whisper)
    - Chat exports (Telegram, Slack)
    - Documents (Markdown, code files)
    """

    text: str = Field(..., min_length=1, description="The raw text content")
    source_type: SourceType = Field(..., description="Type of content source")
    source_file: str | None = Field(default=None, description="Original file path or identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the content was created or captured",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional source-specific metadata (duration, participants, etc.)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Meeting with John about Q4 pricing strategy.",
                    "source_type": "audio",
                    "source_file": "meeting_2024-11-30.json",
                    "metadata": {"duration": 3600, "speakers": ["John", "Me"]},
                }
            ]
        }
    }


class ParsedContent(BaseModel):
    """
    Parsed and structured content ready for LLM enrichment.

    The parser extracts structure from raw content:
    - Chunks: Logical segments for processing
    - Structure: Headers, participants, threads, etc.
    - Hash: For deduplication and idempotency
    """

    raw: RawContent = Field(..., description="Original raw content")
    chunks: list[str] = Field(
        default_factory=list,
        min_length=1,
        description="Text segments for processing (max ~2000 tokens each)",
    )
    structure: dict = Field(
        default_factory=dict,
        description="Extracted structure (headers, speakers, threads)",
    )
    content_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="SHA-256 hash for deduplication",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "raw": {
                        "text": "Meeting with John about Q4 pricing.",
                        "source_type": "audio",
                    },
                    "chunks": ["Meeting with John about Q4 pricing."],
                    "structure": {"speakers": ["John", "Me"], "duration": 3600},
                    "content_hash": "a" * 64,
                }
            ]
        }
    }

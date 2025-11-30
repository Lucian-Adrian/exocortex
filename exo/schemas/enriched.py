"""
Enriched content schemas with LLM-extracted metadata.

These models represent content after LLM processing:
- Intent classification
- Named entity recognition
- Commitment extraction
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Intent(str, Enum):
    """
    Classified intent types for content segments.

    Used to categorize what kind of information is contained.
    """

    DECISION = "decision"  # A choice was made
    COMMITMENT = "commitment"  # Someone promised something
    QUESTION = "question"  # An unanswered question
    IDEA = "idea"  # A creative thought or proposal
    TASK = "task"  # An action item
    UNCLASSIFIED = "unclassified"  # Could not determine intent


class Entity(BaseModel):
    """
    Named entity extracted from content.

    Entities are people, companies, dates, amounts, etc.
    """

    name: str = Field(..., min_length=1, description="Entity name as mentioned in text")
    type: str = Field(
        ...,
        description="Entity type: person, company, project, date, amount, location",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Extraction confidence (0.0 to 1.0)",
    )
    normalized: str | None = Field(
        default=None,
        description="Normalized form (e.g., 'John D.' -> 'John Doe')",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "John",
                    "type": "person",
                    "confidence": 0.95,
                    "normalized": "John Doe",
                }
            ]
        }
    }


class CommitmentStatus(str, Enum):
    """Status of a commitment."""

    OPEN = "open"
    COMPLETE = "complete"
    OVERDUE = "overdue"


class Commitment(BaseModel):
    """
    A promise or commitment extracted from content.

    Tracks who promised what to whom and when.
    """

    from_party: str = Field(..., min_length=1, description="Who made the commitment")
    to_party: str = Field(..., min_length=1, description="Who receives the commitment")
    description: str = Field(..., min_length=1, description="What was promised")
    due_date: datetime | None = Field(default=None, description="When it's due (if mentioned)")
    status: CommitmentStatus = Field(
        default=CommitmentStatus.OPEN,
        description="Current status",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "from_party": "me",
                    "to_party": "John",
                    "description": "Send contract by Monday",
                    "due_date": "2024-12-02T00:00:00Z",
                    "status": "open",
                }
            ]
        }
    }


class EnrichedContent(BaseModel):
    """
    Content enriched with LLM-extracted metadata.

    Contains all extracted information:
    - Intents: What type of information
    - Entities: Who/what is mentioned
    - Commitments: Promises made
    - Summary: TL;DR
    - Topics: Subject tags
    """

    intents: list[Intent] = Field(
        default_factory=list,
        description="Classified intents found in content",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall enrichment confidence",
    )
    entities: list[Entity] = Field(
        default_factory=list,
        description="Extracted named entities",
    )
    commitments: list[Commitment] = Field(
        default_factory=list,
        description="Extracted commitments/promises",
    )
    summary: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="One-paragraph summary of content",
    )
    topics: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Topic tags for categorization",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "intents": ["decision", "commitment"],
                    "confidence": 0.92,
                    "entities": [
                        {"name": "John", "type": "person", "confidence": 0.95}
                    ],
                    "commitments": [
                        {
                            "from_party": "me",
                            "to_party": "John",
                            "description": "Send contract",
                            "status": "open",
                        }
                    ],
                    "summary": "Meeting with John. Agreed on $99/month pricing.",
                    "topics": ["pricing", "business"],
                }
            ]
        }
    }

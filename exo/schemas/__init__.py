"""
Exo Schemas - Pydantic models for the pipeline.

This module exports all schema models for easy importing:

```python
from exo.schemas import RawContent, Memory, QueryResponse, ExoError
```

All models are Pydantic v2 BaseModel subclasses with:
- Full type annotations
- Validation constraints
- JSON schema examples
- Gemini structured output compatibility
"""

# Content models
from exo.schemas.content import (
    ParsedContent,
    RawContent,
    SourceType,
)

# Enrichment models
from exo.schemas.enriched import (
    Commitment,
    CommitmentStatus,
    EnrichedContent,
    Entity,
    Intent,
)

# Error models
from exo.schemas.errors import (
    ErrorCode,
    ExoError,
)

# Memory model
from exo.schemas.memory import Memory

# Query models
from exo.schemas.query import (
    QueryRequest,
    QueryResponse,
    Source,
)

__all__ = [
    # content.py
    "SourceType",
    "RawContent",
    "ParsedContent",
    # enriched.py
    "Intent",
    "Entity",
    "Commitment",
    "CommitmentStatus",
    "EnrichedContent",
    # memory.py
    "Memory",
    # query.py
    "QueryRequest",
    "Source",
    "QueryResponse",
    # errors.py
    "ErrorCode",
    "ExoError",
]

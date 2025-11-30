"""
Exo core pipeline - Pure functions for ingest and query.

Pipeline flow: parse() → enrich() → embed() → store()

All dependencies (Client, AIProvider, EmbeddingProvider) are REQUIRED
parameters - never defaulted to None with hidden creation inside functions.
Use PipelineOrchestrator for managed dependency injection.
"""

from exo.pipeline.parse import parse
from exo.pipeline.enrich import enrich
from exo.pipeline.embed import embed
from exo.pipeline.store import store
from exo.pipeline.query import query
from exo.pipeline.orchestrator import (
    PipelineOrchestrator,
    ingest,
    query as query_convenience,
)

__all__ = [
    # Core pipeline functions
    "parse",
    "enrich",
    "embed",
    "store",
    "query",
    # Orchestrator
    "PipelineOrchestrator",
    # Convenience functions
    "ingest",
]

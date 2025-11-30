"""
Exo AI provider abstractions.

Provides interfaces and implementations for:
- AIProvider: LLM enrichment and generation
- EmbeddingProvider: Vector embedding generation
- GeminiProvider: Google Gemini implementation
"""

from exo.ai.base import AIProvider, EmbeddingProvider
from exo.ai.gemini import GeminiProvider

__all__ = [
    "AIProvider",
    "EmbeddingProvider",
    "GeminiProvider",
]

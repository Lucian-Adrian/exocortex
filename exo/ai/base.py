"""
Abstract base classes for AI providers.

Defines interfaces for:
- AIProvider: LLM enrichment and generation
- EmbeddingProvider: Vector embedding generation

All implementations must follow these interfaces.
"""

from abc import ABC, abstractmethod

from exo.schemas.enriched import EnrichedContent


class AIProvider(ABC):
    """
    Abstract base for AI providers (Gemini, OpenAI, etc.).

    Provides two core capabilities:
    1. Enrichment: Extract structured data from text
    2. Generation: Generate responses given context
    """

    @abstractmethod
    async def enrich(self, text: str) -> EnrichedContent:
        """
        Extract intents, entities, and commitments from text.

        Args:
            text: The raw text to analyze

        Returns:
            EnrichedContent with structured extraction results
        """
        ...

    @abstractmethod
    async def generate(self, prompt: str, context: list[str]) -> str:
        """
        Generate a response given a prompt and context.

        Used for RAG query answering.

        Args:
            prompt: The user's question
            context: Retrieved memory chunks for context

        Returns:
            Generated answer as string
        """
        ...


class EmbeddingProvider(ABC):
    """
    Abstract base for embedding providers.

    Generates vector embeddings for semantic search.
    """

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: The text to embed

        Returns:
            768-dimensional float vector
        """
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in a single call.

        More efficient than calling embed() multiple times.

        Args:
            texts: List of texts to embed

        Returns:
            List of 768-dimensional float vectors
        """
        ...

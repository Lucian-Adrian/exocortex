"""
Pipeline orchestrator.

Owns dependency lifecycle and injects connections into pipeline steps.
Single instance per application for connection pooling.
"""

from supabase import Client

from exo.ai.base import AIProvider, EmbeddingProvider
from exo.ai.gemini import GeminiProvider
from exo.db.client import get_supabase_client
from exo.schemas.content import RawContent, ParsedContent
from exo.schemas.enriched import EnrichedContent
from exo.schemas.memory import Memory
from exo.schemas.query import QueryRequest, QueryResponse
from exo.schemas.errors import ExoError

from exo.pipeline.parse import parse as pipeline_parse
from exo.pipeline.enrich import enrich as pipeline_enrich
from exo.pipeline.embed import embed as pipeline_embed
from exo.pipeline.store import store as pipeline_store
from exo.pipeline.query import query as pipeline_query


class PipelineOrchestrator:
    """
    Owns dependency lifecycle. Injects pooled connections into pipeline steps.
    
    Single instance per application (singleton or DI container).
    Creates default providers if not injected.
    """

    def __init__(
        self,
        client: Client | None = None,
        ai_provider: AIProvider | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        """
        Initialize orchestrator with optional dependencies.
        
        Args:
            client: Supabase client (created if not provided).
            ai_provider: AI provider for enrichment/generation (GeminiProvider if not provided).
            embedding_provider: Embedding provider (uses ai_provider if it implements EmbeddingProvider).
        """
        # Create once, reuse everywhere (connection pooling)
        self._client = client or get_supabase_client()
        self._ai = ai_provider or GeminiProvider()
        
        # Use AI provider for embeddings if it implements EmbeddingProvider
        if embedding_provider is not None:
            self._embedder = embedding_provider
        elif isinstance(self._ai, EmbeddingProvider):
            self._embedder = self._ai
        else:
            # Fallback to GeminiProvider which implements both
            self._embedder = GeminiProvider()

    @property
    def client(self) -> Client:
        """Get the Supabase client."""
        return self._client

    @property
    def ai_provider(self) -> AIProvider:
        """Get the AI provider."""
        return self._ai

    @property
    def embedding_provider(self) -> EmbeddingProvider:
        """Get the embedding provider."""
        return self._embedder

    async def ingest(self, content: RawContent) -> Memory | ExoError:
        """
        Full pipeline: parse → enrich → embed → store.
        
        Short-circuits on any ExoError.
        
        Args:
            content: Raw content to ingest.
            
        Returns:
            Memory with ID populated, or ExoError on failure.
        """
        # Step 1: Parse
        parsed = await pipeline_parse(content)
        if isinstance(parsed, ExoError):
            return parsed

        # Step 2: Enrich
        enriched = await pipeline_enrich(parsed, provider=self._ai)
        if isinstance(enriched, ExoError):
            return enriched

        # Step 3: Embed
        memory = await pipeline_embed(
            enriched,
            provider=self._embedder,
            source_type=content.source_type,
            source_file=content.source_file,
            original_content=content.text,
        )
        if isinstance(memory, ExoError):
            return memory

        # Step 4: Store
        return await pipeline_store(memory, client=self._client)

    async def query(self, request: QueryRequest) -> QueryResponse | ExoError:
        """
        RAG query with injected dependencies.
        
        Args:
            request: Query request with question and parameters.
            
        Returns:
            QueryResponse with answer and sources, or ExoError on failure.
        """
        return await pipeline_query(
            request,
            client=self._client,
            provider=self._ai,
            embedding_provider=self._embedder,
        )

    async def parse(self, content: RawContent) -> ParsedContent | ExoError:
        """
        Parse content without full pipeline.
        
        Useful for debugging or partial processing.
        
        Args:
            content: Raw content to parse.
            
        Returns:
            ParsedContent or ExoError.
        """
        return await pipeline_parse(content)

    async def enrich(self, content: ParsedContent) -> EnrichedContent | ExoError:
        """
        Enrich content without full pipeline.
        
        Args:
            content: Parsed content to enrich.
            
        Returns:
            EnrichedContent or ExoError.
        """
        return await pipeline_enrich(content, provider=self._ai)

    async def embed(self, content: EnrichedContent) -> Memory | ExoError:
        """
        Create embedding without full pipeline.
        
        Args:
            content: Enriched content to embed.
            
        Returns:
            Memory with embedding, or ExoError.
        """
        return await pipeline_embed(content, provider=self._embedder)

    async def store(self, memory: Memory) -> Memory | ExoError:
        """
        Store memory without full pipeline.
        
        Args:
            memory: Memory to store.
            
        Returns:
            Memory with ID, or ExoError.
        """
        return await pipeline_store(memory, client=self._client)


# Convenience functions for simple usage

async def ingest(
    content: RawContent,
    orchestrator: PipelineOrchestrator | None = None,
) -> Memory | ExoError:
    """
    Convenience wrapper for ingest.
    
    For advanced usage, instantiate PipelineOrchestrator directly.
    
    Args:
        content: Raw content to ingest.
        orchestrator: Optional orchestrator (created if not provided).
        
    Returns:
        Memory with ID, or ExoError.
    """
    orch = orchestrator or PipelineOrchestrator()
    return await orch.ingest(content)


async def query(
    request: QueryRequest,
    orchestrator: PipelineOrchestrator | None = None,
) -> QueryResponse | ExoError:
    """
    Convenience wrapper for query.
    
    For advanced usage, instantiate PipelineOrchestrator directly.
    
    Args:
        request: Query request.
        orchestrator: Optional orchestrator (created if not provided).
        
    Returns:
        QueryResponse or ExoError.
    """
    orch = orchestrator or PipelineOrchestrator()
    return await orch.query(request)

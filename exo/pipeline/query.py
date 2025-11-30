"""
Query pipeline step.

Handles RAG retrieval and answer generation.
"""

from supabase import Client

from exo.ai.base import AIProvider, EmbeddingProvider
from exo.db.queries import search_semantic
from exo.schemas.query import QueryRequest, QueryResponse, Source
from exo.schemas.errors import ExoError, ErrorCode


async def query(
    request: QueryRequest,
    client: Client,
    provider: AIProvider,
    embedding_provider: EmbeddingProvider | None = None,
) -> QueryResponse | ExoError:
    """
    Execute RAG query pipeline.
    
    Steps:
    1. Embed the question
    2. Search for semantically similar memories
    3. Generate answer with context
    4. Return QueryResponse with sources
    
    Args:
        request: Query request with question and parameters.
        client: Supabase client (REQUIRED - pooled connection).
        provider: AI provider for generation (REQUIRED).
        embedding_provider: Provider for embeddings (defaults to provider if it's also EmbeddingProvider).
        
    Returns:
        QueryResponse with answer and sources, or ExoError on failure.
    """
    try:
        # Use AI provider for embeddings if it implements EmbeddingProvider
        embedder = embedding_provider
        if embedder is None and isinstance(provider, EmbeddingProvider):
            embedder = provider
        
        if embedder is None:
            return ExoError(
                code=ErrorCode.QUERY_ERROR,
                message="No embedding provider available for query",
                details={},
                recoverable=False,
            )
        
        # Step 1: Embed the question
        question_embedding = await embedder.embed(request.question)
        
        if not question_embedding:
            return ExoError(
                code=ErrorCode.EMBED_ERROR,
                message="Failed to embed question",
                details={"question": request.question},
                recoverable=True,
            )
        
        # Step 2: Semantic search
        search_result = await search_semantic(
            client,
            embedding=question_embedding,
            top_k=request.top_k,
            threshold=request.similarity_threshold,
            filters=request.filters if request.filters else None,
        )
        
        if search_result.error:
            return ExoError(
                code=ErrorCode.QUERY_ERROR,
                message=f"Search failed: {search_result.error}",
                details={"db_error": search_result.error},
                recoverable=True,
            )
        
        memories = search_result.data or []
        
        # Build context from retrieved memories
        context: list[str] = []
        sources: list[Source] = []
        commitments: list[dict] = []
        
        for memory in memories:
            # Add content to context
            content = memory.get("content", "")
            summary = memory.get("summary", content)
            similarity = memory.get("similarity", 0.0)
            
            context.append(summary)
            
            # Build source
            sources.append(Source(
                memory_id=str(memory.get("id", "")),
                content_preview=summary[:200] if summary else "",
                similarity=similarity,
                source_file=memory.get("source_file"),
            ))
            
            # Collect commitments
            mem_commitments = memory.get("commitments", [])
            if isinstance(mem_commitments, list):
                commitments.extend(mem_commitments)
        
        # Step 3: Generate answer
        if context:
            answer = await provider.generate(request.question, context)
        else:
            answer = f"I don't have any relevant information to answer: {request.question}"
        
        # Calculate confidence based on best similarity
        confidence = max((s.similarity for s in sources), default=0.0)
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            commitments=commitments,
            confidence=confidence,
        )
        
    except ConnectionError as e:
        return ExoError(
            code=ErrorCode.AI_UNAVAILABLE,
            message=f"Provider connection failed: {e}",
            details={"error_type": "ConnectionError"},
            recoverable=True,
        )
    except Exception as e:
        return ExoError(
            code=ErrorCode.QUERY_ERROR,
            message=f"Query failed: {e}",
            details={"error_type": type(e).__name__},
            recoverable=True,
        )

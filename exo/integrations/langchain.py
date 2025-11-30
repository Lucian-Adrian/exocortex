"""
LangChain integration for Exo.

Provides ExoRetriever that implements LangChain's BaseRetriever interface,
allowing Exo to be used as a retriever in LangChain RAG pipelines.

Usage:
    from exo.integrations.langchain import ExoRetriever

    retriever = ExoRetriever(client=supabase_client, embedding_provider=provider)
    docs = retriever.invoke("What commitments do I have?")
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, List

try:
    from langchain_core.callbacks import CallbackManagerForRetrieverRun
    from langchain_core.documents import Document
    from langchain_core.retrievers import BaseRetriever

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Create stub classes for type hints when langchain is not installed
    BaseRetriever = object  # type: ignore
    Document = object  # type: ignore
    CallbackManagerForRetrieverRun = object  # type: ignore

if TYPE_CHECKING:
    from supabase import Client
    from exo.ai.base import EmbeddingProvider


class ExoRetriever(BaseRetriever):  # type: ignore[misc]
    """
    LangChain retriever backed by Exo's semantic search.

    This retriever:
    - Embeds the query using the configured embedding provider
    - Searches Exo's memory store for semantically similar content
    - Returns LangChain Document objects with metadata

    Attributes:
        client: Supabase client for database access
        embedding_provider: Provider for generating query embeddings
        top_k: Maximum number of documents to return (default: 5)
        similarity_threshold: Minimum similarity score (default: 0.7)
    """

    # Pydantic fields for LangChain BaseRetriever
    client: Any = None
    embedding_provider: Any = None
    top_k: int = 5
    similarity_threshold: float = 0.7

    class Config:
        """Pydantic config for arbitrary types."""
        arbitrary_types_allowed = True

    def __init__(
        self,
        client: "Client",
        embedding_provider: "EmbeddingProvider",
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        **kwargs: Any,
    ) -> None:
        """
        Initialize ExoRetriever.

        Args:
            client: Supabase client for database access
            embedding_provider: Provider for generating query embeddings
            top_k: Maximum number of documents to return
            similarity_threshold: Minimum similarity score for results
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "langchain-core is required for ExoRetriever. "
                "Install with: pip install 'exo-brain[langchain]'"
            )

        super().__init__(
            client=client,
            embedding_provider=embedding_provider,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            **kwargs,
        )

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> List[Document]:
        """
        Synchronously retrieve relevant documents.

        Args:
            query: The search query
            run_manager: Optional callback manager

        Returns:
            List of LangChain Document objects
        """
        # Run async version in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, need to use run_coroutine_threadsafe
                import concurrent.futures
                future = asyncio.run_coroutine_threadsafe(
                    self._aget_relevant_documents(query, run_manager=run_manager),
                    loop,
                )
                return future.result(timeout=30)
            else:
                return loop.run_until_complete(
                    self._aget_relevant_documents(query, run_manager=run_manager)
                )
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(
                self._aget_relevant_documents(query, run_manager=run_manager)
            )

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> List[Document]:
        """
        Asynchronously retrieve relevant documents.

        Args:
            query: The search query
            run_manager: Optional callback manager

        Returns:
            List of LangChain Document objects
        """
        from exo.db.queries import search_semantic

        # Generate embedding for query
        query_embedding = await self.embedding_provider.embed(query)

        # Search for similar documents
        result = await search_semantic(
            client=self.client,
            embedding=query_embedding,
            limit=self.top_k,
            threshold=self.similarity_threshold,
        )

        # Handle errors
        if hasattr(result, "error") and result.error:
            return []

        # Convert to LangChain Documents
        documents: List[Document] = []
        memories = result.data if hasattr(result, "data") else result

        if not memories:
            return documents

        for memory in memories:
            # Extract content and metadata
            content = memory.get("summary", memory.get("content", ""))
            metadata = {
                "memory_id": str(memory.get("id", "")),
                "source_type": memory.get("source_type", ""),
                "source_file": memory.get("source_file", ""),
                "similarity": memory.get("similarity", 0.0),
                "created_at": memory.get("created_at", ""),
                "intents": memory.get("intents", []),
                "entities": memory.get("entities", {}),
            }

            documents.append(Document(page_content=content, metadata=metadata))

        return documents

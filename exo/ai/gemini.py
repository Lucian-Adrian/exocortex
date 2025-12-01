"""
Google Gemini AI provider implementation.

Implements AIProvider and EmbeddingProvider using:
- gemini-2.5-flash-lite for enrichment and generation (configurable via GEMINI_MODEL)
- text-embedding-004 for embeddings (768 dimensions, configurable via GEMINI_EMBEDDING_MODEL)

Model configuration is hot-swappable via environment variables.
"""

import asyncio
import json
import os
from typing import Any

import google.generativeai as genai

from exo.ai.base import AIProvider, EmbeddingProvider
from exo.config import get_settings
from exo.schemas.enriched import (
    Commitment,
    CommitmentStatus,
    EnrichedContent,
    Entity,
    Intent,
)


# System prompts for different tasks
ENRICH_SYSTEM_PROMPT = """You are an expert at analyzing conversations and documents to extract structured information.

Your task is to analyze the provided text and extract:
1. **Intents**: Classify each segment (decision, commitment, question, idea, task, unclassified)
2. **Entities**: Named entities (people, companies, projects, dates, amounts)
3. **Commitments**: Promises made (who promised what to whom, and when)
4. **Summary**: A concise one-paragraph summary
5. **Topics**: 1-5 topic tags

Be precise and only extract information that is clearly stated or strongly implied.

Return your response as valid JSON with this exact structure:
{
    "intents": ["decision", "commitment", ...],
    "confidence": 0.92,
    "entities": [{"name": "...", "type": "person|company|project|date|amount", "confidence": 0.95, "normalized": "..."}],
    "commitments": [{"from_party": "...", "to_party": "...", "description": "...", "due_date": "YYYY-MM-DD or null", "status": "open"}],
    "summary": "One paragraph summary",
    "topics": ["topic1", "topic2"]
}"""

GENERATE_SYSTEM_PROMPT = """You are a personal memory assistant with access to the user's past conversations, notes, and documents.

Your role is to:
1. Answer questions based on the provided context
2. Cite specific sources when possible
3. Highlight any commitments or action items
4. Be concise but complete

If the context doesn't contain enough information to answer, say so clearly."""


class GeminiProvider(AIProvider, EmbeddingProvider):
    """
    Google Gemini implementation for enrichment and embeddings.

    Supports both synchronous and asynchronous usage.
    Implements both AIProvider and EmbeddingProvider interfaces.

    Model configuration is hot-swappable via environment variables:
    - GEMINI_MODEL: Model for enrichment/generation (default: gemini-2.5-flash-lite)
    - GEMINI_EMBEDDING_MODEL: Model for embeddings (default: text-embedding-004)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        """
        Initialize Gemini provider.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model for enrichment/generation (defaults to GEMINI_MODEL env var or gemini-2.5-flash-lite)
            embedding_model: Model for embeddings (defaults to GEMINI_EMBEDDING_MODEL env var or text-embedding-004)
        """
        # Load settings for defaults
        settings = get_settings()

        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model or settings.GEMINI_MODEL
        self._embedding_model = embedding_model or settings.GEMINI_EMBEDDING_MODEL

        # Configure the API
        genai.configure(api_key=self._api_key)

        # Create model instance with JSON response mode for enrichment
        self._gen_model = genai.GenerativeModel(
            model_name=self._model,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            ),
        )

    async def enrich(self, text: str) -> EnrichedContent:
        """
        Extract structured information from text using Gemini.

        Uses JSON output mode to ensure valid schema.
        """
        prompt = f"""{ENRICH_SYSTEM_PROMPT}

Analyze the following text:

{text}"""

        # Make the API call
        response = await asyncio.to_thread(
            self._gen_model.generate_content,
            prompt,
        )

        # Parse the response
        result = self._parse_enrich_response(response)
        return result


    def _parse_enrich_response(self, response: Any) -> EnrichedContent:
        """Parse Gemini response into EnrichedContent."""
        import json

        # Extract JSON from response
        text = response.text
        data = json.loads(text)

        # Convert to Pydantic models with safe defaults
        intents = [Intent(i) for i in data.get("intents", []) if i in [e.value for e in Intent]]
        
        # Handle entities - might be list or dict
        entities_data = data.get("entities", [])
        entities = []
        if isinstance(entities_data, list):
            for e in entities_data:
                if isinstance(e, dict) and "name" in e:
                    entities.append(Entity(
                        name=e["name"],
                        type=e.get("type", "unknown"),
                        confidence=e.get("confidence", 0.8),
                        normalized=e.get("normalized"),
                    ))
        elif isinstance(entities_data, dict):
            # Handle dict format {type: [names]}
            for entity_type, names in entities_data.items():
                if isinstance(names, list):
                    for name in names:
                        if isinstance(name, str):
                            entities.append(Entity(
                                name=name,
                                type=entity_type,
                                confidence=0.8,
                            ))
                        elif isinstance(name, dict) and "name" in name:
                            entities.append(Entity(
                                name=name["name"],
                                type=entity_type,
                                confidence=name.get("confidence", 0.8),
                                normalized=name.get("normalized"),
                            ))
        
        # Handle commitments
        commitments_data = data.get("commitments", [])
        commitments = []
        for c in commitments_data:
            if isinstance(c, dict) and all(k in c for k in ["from_party", "to_party", "description"]):
                commitments.append(Commitment(
                    from_party=c["from_party"],
                    to_party=c["to_party"],
                    description=c["description"],
                    due_date=c.get("due_date"),
                    status=CommitmentStatus(c.get("status", "open")) if c.get("status") in ["open", "complete", "overdue"] else CommitmentStatus.OPEN,
                ))

        # Ensure summary is not empty (required by schema)
        summary = data.get("summary", "") or "No summary available."
        
        return EnrichedContent(
            intents=intents,
            confidence=data.get("confidence", 0.8),
            entities=entities,
            commitments=commitments,
            summary=summary,
            topics=data.get("topics", []),
        )

    async def generate(self, prompt: str, context: list[str]) -> str:
        """
        Generate a response using RAG context.

        Args:
            prompt: The user's question
            context: Retrieved memory chunks

        Returns:
            Generated answer
        """
        # Build the context string
        context_str = "\n\n---\n\n".join(context) if context else "No relevant context found."

        # Build the full prompt with system instruction inline
        full_prompt = f"""{GENERATE_SYSTEM_PROMPT}

Context from your memory:
{context_str}

---

Question: {prompt}

Please answer based on the context above."""

        # Create a model without JSON response mode for generation
        gen_model = genai.GenerativeModel(model_name=self._model)

        # Make the API call
        response = await asyncio.to_thread(
            gen_model.generate_content,
            full_prompt,
        )

        return response.text

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Returns 768-dimensional vector.
        """
        response = await asyncio.to_thread(
            genai.embed_content,
            model=self._embedding_model,
            content=text,
        )

        # Extract the embedding vector
        return list(response["embedding"])

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        More efficient than calling embed() repeatedly.
        """
        if not texts:
            return []

        # Process each text individually (Gemini SDK handles one at a time)
        results = []
        for txt in texts:
            response = await asyncio.to_thread(
                genai.embed_content,
                model=self._embedding_model,
                content=txt,
            )
            results.append(list(response["embedding"]))

        return results


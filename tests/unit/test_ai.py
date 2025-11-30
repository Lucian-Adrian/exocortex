"""
Unit tests for AI provider layer.

Tests abstract interfaces and mocked implementations.
Integration tests requiring API keys are in tests/integration/.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from exo.ai.base import AIProvider, EmbeddingProvider
from exo.ai.gemini import GeminiProvider
from exo.schemas.enriched import EnrichedContent, Intent


# =============================================================================
# Abstract Interface Tests
# =============================================================================


class TestAIProviderABC:
    """Tests for AIProvider abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        """AIProvider cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            AIProvider()  # type: ignore
        assert "abstract" in str(exc_info.value).lower()

    def test_subclass_must_implement_enrich(self) -> None:
        """Subclass must implement enrich method."""

        class IncompleteProvider(AIProvider):
            async def generate(self, prompt: str, context: list[str]) -> str:
                return "test"

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore

    def test_subclass_must_implement_generate(self) -> None:
        """Subclass must implement generate method."""

        class IncompleteProvider(AIProvider):
            async def enrich(self, text: str) -> EnrichedContent:
                return EnrichedContent(confidence=0.9, summary="test")

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore


class TestEmbeddingProviderABC:
    """Tests for EmbeddingProvider abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        """EmbeddingProvider cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            EmbeddingProvider()  # type: ignore
        assert "abstract" in str(exc_info.value).lower()

    def test_subclass_must_implement_embed(self) -> None:
        """Subclass must implement embed method."""

        class IncompleteProvider(EmbeddingProvider):
            async def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.1] * 768]

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore

    def test_subclass_must_implement_embed_batch(self) -> None:
        """Subclass must implement embed_batch method."""

        class IncompleteProvider(EmbeddingProvider):
            async def embed(self, text: str) -> list[float]:
                return [0.1] * 768

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore


# =============================================================================
# Gemini Provider Tests (Mocked)
# =============================================================================


class TestGeminiProviderInit:
    """Tests for GeminiProvider initialization."""

    def test_init_with_api_key(self) -> None:
        """GeminiProvider can be initialized with explicit API key and models."""
        with patch("exo.ai.gemini.genai.configure"):
            with patch("exo.ai.gemini.genai.GenerativeModel"):
                with patch("exo.ai.gemini.get_settings") as mock_settings:
                    mock_settings.return_value.GEMINI_API_KEY = "default-key"
                    mock_settings.return_value.GEMINI_MODEL = "gemini-2.5-flash-lite"
                    mock_settings.return_value.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

                    provider = GeminiProvider(
                        api_key="test-key",
                        model="gemini-2.5-flash",
                        embedding_model="text-embedding-004",
                    )
                    assert provider._api_key == "test-key"
                    assert provider._model == "gemini-2.5-flash"
                    assert provider._embedding_model == "text-embedding-004"

    def test_init_with_custom_models(self) -> None:
        """GeminiProvider accepts custom model names."""
        with patch("exo.ai.gemini.genai.configure"):
            with patch("exo.ai.gemini.genai.GenerativeModel"):
                with patch("exo.ai.gemini.get_settings") as mock_settings:
                    mock_settings.return_value.GEMINI_API_KEY = "default-key"
                    mock_settings.return_value.GEMINI_MODEL = "gemini-2.5-flash-lite"
                    mock_settings.return_value.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

                    provider = GeminiProvider(
                        api_key="test-key",
                        model="gemini-1.5-pro",
                        embedding_model="text-embedding-preview-0409",
                    )
                    assert provider._model == "gemini-1.5-pro"
                    assert provider._embedding_model == "text-embedding-preview-0409"

    def test_init_uses_settings_defaults(self) -> None:
        """GeminiProvider uses settings for defaults when no args provided."""
        with patch("exo.ai.gemini.get_settings") as mock_settings:
            # Create a proper mock settings object
            mock_settings_obj = MagicMock()
            mock_settings_obj.GEMINI_API_KEY = "settings-key"
            mock_settings_obj.GEMINI_MODEL = "gemini-2.5-flash-lite"
            mock_settings_obj.GEMINI_EMBEDDING_MODEL = "text-embedding-004"
            mock_settings.return_value = mock_settings_obj

            with patch("exo.ai.gemini.genai.configure"):
                with patch("exo.ai.gemini.genai.GenerativeModel"):
                    provider = GeminiProvider()
                    assert provider._api_key == "settings-key"
                    assert provider._model == "gemini-2.5-flash-lite"
                    assert provider._embedding_model == "text-embedding-004"



class TestGeminiProviderEnrich:
    """Tests for GeminiProvider.enrich() method."""

    @pytest.mark.asyncio
    async def test_enrich_parses_response(self) -> None:
        """enrich() correctly parses Gemini response."""
        with patch("exo.ai.gemini.genai.configure"):
            with patch("exo.ai.gemini.genai.GenerativeModel") as mock_model_class:
                with patch("exo.ai.gemini.get_settings") as mock_settings:
                    mock_settings.return_value.GEMINI_API_KEY = "test-key"
                    mock_settings.return_value.GEMINI_MODEL = "gemini-2.5-flash-lite"
                    mock_settings.return_value.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

                    # Setup mock
                    mock_model = MagicMock()
                    mock_model_class.return_value = mock_model

                    mock_response = MagicMock()
                    mock_response.text = """{
                        "intents": ["decision", "commitment"],
                        "confidence": 0.92,
                        "entities": [
                            {"name": "John", "type": "person", "confidence": 0.95}
                        ],
                        "commitments": [
                            {
                                "from_party": "me",
                                "to_party": "John",
                                "description": "send contract",
                                "status": "open"
                            }
                        ],
                        "summary": "Meeting with John about pricing.",
                        "topics": ["business", "pricing"]
                    }"""
                    mock_model.generate_content.return_value = mock_response

                    provider = GeminiProvider(api_key="test-key")
                    result = await provider.enrich("Meeting with John. Agreed on $99/month.")

                    # Verify result
                    assert isinstance(result, EnrichedContent)
                    assert Intent.DECISION in result.intents
                    assert Intent.COMMITMENT in result.intents
                    assert result.confidence == 0.92
                    assert len(result.entities) == 1
                    assert result.entities[0].name == "John"
                    assert len(result.commitments) == 1
                    assert result.commitments[0].to_party == "John"
                    assert result.summary == "Meeting with John about pricing."
                    assert "business" in result.topics



class TestGeminiProviderGenerate:
    """Tests for GeminiProvider.generate() method."""

    @pytest.mark.asyncio
    async def test_generate_returns_text(self) -> None:
        """generate() returns text response."""
        with patch("exo.ai.gemini.genai.configure"):
            with patch("exo.ai.gemini.genai.GenerativeModel") as mock_model_class:
                with patch("exo.ai.gemini.get_settings") as mock_settings:
                    mock_settings.return_value.GEMINI_API_KEY = "test-key"
                    mock_settings.return_value.GEMINI_MODEL = "gemini-2.5-flash-lite"
                    mock_settings.return_value.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

                    mock_model = MagicMock()
                    mock_model_class.return_value = mock_model

                    mock_response = MagicMock()
                    mock_response.text = "You promised John to send the contract by Monday."
                    mock_model.generate_content.return_value = mock_response

                    provider = GeminiProvider(api_key="test-key")
                    result = await provider.generate(
                        prompt="What did I promise John?",
                        context=["Meeting with John. I'll send contract Monday."],
                    )

                    assert "contract" in result.lower()
                    assert "John" in result or "john" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_handles_empty_context(self) -> None:
        """generate() works with empty context."""
        with patch("exo.ai.gemini.genai.configure"):
            with patch("exo.ai.gemini.genai.GenerativeModel") as mock_model_class:
                with patch("exo.ai.gemini.get_settings") as mock_settings:
                    mock_settings.return_value.GEMINI_API_KEY = "test-key"
                    mock_settings.return_value.GEMINI_MODEL = "gemini-2.5-flash-lite"
                    mock_settings.return_value.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

                    mock_model = MagicMock()
                    mock_model_class.return_value = mock_model

                    mock_response = MagicMock()
                    mock_response.text = "I don't have enough context to answer."
                    mock_model.generate_content.return_value = mock_response

                    provider = GeminiProvider(api_key="test-key")
                    result = await provider.generate(prompt="Random question?", context=[])

                    assert isinstance(result, str)
                    assert len(result) > 0



class TestGeminiProviderEmbed:
    """Tests for GeminiProvider.embed() methods."""

    @pytest.mark.asyncio
    async def test_embed_returns_vector(self) -> None:
        """embed() returns 768-dimensional vector."""
        with patch("exo.ai.gemini.genai.configure"):
            with patch("exo.ai.gemini.genai.GenerativeModel"):
                with patch("exo.ai.gemini.genai.embed_content") as mock_embed:
                    with patch("exo.ai.gemini.get_settings") as mock_settings:
                        mock_settings.return_value.GEMINI_API_KEY = "test-key"
                        mock_settings.return_value.GEMINI_MODEL = "gemini-2.5-flash-lite"
                        mock_settings.return_value.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

                        # Mock embedding response
                        mock_embed.return_value = {"embedding": [0.1] * 768}

                        provider = GeminiProvider(api_key="test-key")
                        result = await provider.embed("Test text")

                        assert isinstance(result, list)
                        assert len(result) == 768
                        assert all(isinstance(v, float) for v in result)

    @pytest.mark.asyncio
    async def test_embed_batch_returns_multiple_vectors(self) -> None:
        """embed_batch() returns multiple vectors."""
        with patch("exo.ai.gemini.genai.configure"):
            with patch("exo.ai.gemini.genai.GenerativeModel"):
                with patch("exo.ai.gemini.genai.embed_content") as mock_embed:
                    with patch("exo.ai.gemini.get_settings") as mock_settings:
                        mock_settings.return_value.GEMINI_API_KEY = "test-key"
                        mock_settings.return_value.GEMINI_MODEL = "gemini-2.5-flash-lite"
                        mock_settings.return_value.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

                        # Mock returns different vectors for each call
                        mock_embed.return_value = {"embedding": [0.1] * 768}

                        provider = GeminiProvider(api_key="test-key")
                        result = await provider.embed_batch(["text1", "text2", "text3"])

                        assert isinstance(result, list)
                        assert len(result) == 3
                        for vec in result:
                            assert len(vec) == 768

    @pytest.mark.asyncio
    async def test_embed_batch_empty_input(self) -> None:
        """embed_batch() handles empty input."""
        with patch("exo.ai.gemini.genai.configure"):
            with patch("exo.ai.gemini.genai.GenerativeModel"):
                with patch("exo.ai.gemini.get_settings") as mock_settings:
                    mock_settings.return_value.GEMINI_API_KEY = "test-key"
                    mock_settings.return_value.GEMINI_MODEL = "gemini-2.5-flash-lite"
                    mock_settings.return_value.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

                    provider = GeminiProvider(api_key="test-key")
                    result = await provider.embed_batch([])

                    assert result == []



class TestGeminiProviderImplementsInterfaces:
    """Tests that GeminiProvider correctly implements interfaces."""

    def test_implements_ai_provider(self) -> None:
        """GeminiProvider implements AIProvider."""
        with patch("exo.ai.gemini.genai.configure"):
            with patch("exo.ai.gemini.genai.GenerativeModel"):
                with patch("exo.ai.gemini.get_settings") as mock_settings:
                    mock_settings.return_value.GEMINI_API_KEY = "test-key"
                    mock_settings.return_value.GEMINI_MODEL = "gemini-2.5-flash-lite"
                    mock_settings.return_value.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

                    provider = GeminiProvider(api_key="test-key")
                    assert isinstance(provider, AIProvider)

    def test_implements_embedding_provider(self) -> None:
        """GeminiProvider implements EmbeddingProvider."""
        with patch("exo.ai.gemini.genai.configure"):
            with patch("exo.ai.gemini.genai.GenerativeModel"):
                with patch("exo.ai.gemini.get_settings") as mock_settings:
                    mock_settings.return_value.GEMINI_API_KEY = "test-key"
                    mock_settings.return_value.GEMINI_MODEL = "gemini-2.5-flash-lite"
                    mock_settings.return_value.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

                    provider = GeminiProvider(api_key="test-key")
                    assert isinstance(provider, EmbeddingProvider)


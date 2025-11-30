"""
Unit tests for API routes.

Tests endpoint functionality with mocked dependencies.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_settings():
    """Create mock settings to avoid env var requirements."""
    with patch("exo.config.get_settings") as mock:
        settings = MagicMock()
        settings.SUPABASE_URL = "https://test.supabase.co"
        settings.SUPABASE_KEY = "test-key"
        settings.GEMINI_API_KEY = "test-gemini-key"
        settings.GEMINI_MODEL = "gemini-2.5-flash-lite"
        settings.GEMINI_EMBEDDING_MODEL = "text-embedding-004"
        settings.EXO_API_KEY = None  # No auth required
        mock.return_value = settings
        yield mock


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator."""
    orchestrator = MagicMock()
    orchestrator.ingest = AsyncMock()
    orchestrator.query = AsyncMock()
    orchestrator._client = MagicMock()
    orchestrator._embedding_provider = MagicMock()
    orchestrator._embedding_provider.embed = AsyncMock(return_value=[0.1] * 768)
    return orchestrator


@pytest.fixture
def client(mock_settings, mock_orchestrator):
    """Create test client with mocked dependencies."""
    with patch("exo.ai.gemini.genai.configure"):
        with patch("exo.ai.gemini.genai.GenerativeModel"):
            with patch("exo.db.client.create_client"):
                # Patch the orchestrator creation in lifespan
                with patch("exo.api.app.PipelineOrchestrator", return_value=mock_orchestrator):
                    from exo.api.app import create_app

                    app = create_app()

                    with TestClient(app) as test_client:
                        yield test_client


# =============================================================================
# Health Endpoint Tests
# =============================================================================


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """Health endpoint returns status ok."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert data["service"] == "exo"

    def test_root_returns_welcome(self, client: TestClient) -> None:
        """Root endpoint returns welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["docs"] == "/docs"


# =============================================================================
# Ingest Endpoint Tests
# =============================================================================


class TestIngestEndpoint:
    """Tests for /api/v1/ingest endpoint."""

    def test_ingest_success(self, client: TestClient, mock_orchestrator) -> None:
        """Ingest endpoint returns memory on success."""
        from exo.schemas.content import SourceType
        from exo.schemas.memory import Memory

        # Mock successful ingest
        mock_memory = Memory(
            content="Test content",
            summary="Test summary",
            topics=["test"],
            source_type=SourceType.MARKDOWN,
        )
        mock_orchestrator.ingest.return_value = mock_memory

        response = client.post(
            "/api/v1/ingest",
            json={"text": "Test content", "source_type": "markdown"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "memory" in data
        assert data["memory"]["summary"] == "Test summary"

    def test_ingest_error(self, client: TestClient, mock_orchestrator) -> None:
        """Ingest endpoint returns error on failure."""
        from exo.schemas.errors import ErrorCode, ExoError

        # Mock error response
        mock_orchestrator.ingest.return_value = ExoError(
            code=ErrorCode.PARSE_ERROR,
            message="Failed to parse content",
        )

        response = client.post(
            "/api/v1/ingest",
            json={"text": "Invalid content", "source_type": "markdown"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "PARSE_ERROR"


# =============================================================================
# Query Endpoint Tests
# =============================================================================


class TestQueryEndpoint:
    """Tests for /api/v1/query endpoint."""

    def test_query_success(self, client: TestClient, mock_orchestrator) -> None:
        """Query endpoint returns response on success."""
        from exo.schemas.query import QueryResponse, Source

        # Mock successful query
        mock_response = QueryResponse(
            answer="Test answer",
            sources=[Source(
                memory_id="test-id",
                content_preview="Source text",
                similarity=0.9,
            )],
            confidence=0.85,
        )
        mock_orchestrator.query.return_value = mock_response

        response = client.post(
            "/api/v1/query",
            json={"question": "Test question?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["answer"] == "Test answer"
        assert len(data["sources"]) == 1

    def test_query_error(self, client: TestClient, mock_orchestrator) -> None:
        """Query endpoint returns error on failure."""
        from exo.schemas.errors import ErrorCode, ExoError

        # Mock error response
        mock_orchestrator.query.return_value = ExoError(
            code=ErrorCode.AI_UNAVAILABLE,
            message="AI service unavailable",
        )

        response = client.post(
            "/api/v1/query",
            json={"question": "Test question?"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


# =============================================================================
# Webhook Tests
# =============================================================================


class TestWebhookEndpoints:
    """Tests for webhook endpoints."""

    def test_webhook_ingest(self, client: TestClient, mock_orchestrator) -> None:
        """Webhook ingest endpoint works with simplified payload."""
        from exo.schemas.content import SourceType
        from exo.schemas.memory import Memory

        mock_memory = Memory(
            content="Webhook content",
            summary="Webhook summary",
            topics=["webhook"],
            source_type=SourceType.MARKDOWN,
        )
        mock_orchestrator.ingest.return_value = mock_memory

        response = client.post(
            "/webhook/ingest",
            json={"text": "Webhook content", "source_type": "markdown"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"] == "Webhook summary"

    def test_webhook_query(self, client: TestClient, mock_orchestrator) -> None:
        """Webhook query endpoint works with simplified payload."""
        from exo.schemas.query import QueryResponse

        mock_response = QueryResponse(
            answer="Webhook answer",
            sources=[],
            confidence=0.8,
        )
        mock_orchestrator.query.return_value = mock_response

        response = client.post(
            "/webhook/query",
            json={"question": "Webhook question?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["answer"] == "Webhook answer"


# =============================================================================
# Middleware Tests
# =============================================================================


class TestMiddleware:
    """Tests for API middleware."""

    def test_auth_not_required_for_health(self, client: TestClient) -> None:
        """Health endpoint doesn't require auth."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_auth_required_when_key_set(self, mock_settings) -> None:
        """Protected endpoints require auth when key is set."""
        # Set API key requirement
        with patch.dict("os.environ", {"EXO_API_KEY": "secret-key"}):
            with patch("exo.ai.gemini.genai.configure"):
                with patch("exo.ai.gemini.genai.GenerativeModel"):
                    with patch("exo.db.client.create_client"):
                        from exo.api.app import create_app

                        app = create_app()
                        app.state.orchestrator = MagicMock()

                        with TestClient(app) as test_client:
                            # Request without key should fail
                            response = test_client.post(
                                "/api/v1/ingest",
                                json={"text": "test", "source_type": "markdown"},
                            )
                            assert response.status_code == 401

                            # Request with wrong key should fail
                            response = test_client.post(
                                "/api/v1/ingest",
                                json={"text": "test", "source_type": "markdown"},
                                headers={"X-API-Key": "wrong-key"},
                            )
                            assert response.status_code == 401

                            # Request with correct key should work
                            response = test_client.post(
                                "/api/v1/ingest",
                                json={"text": "test", "source_type": "markdown"},
                                headers={"X-API-Key": "secret-key"},
                            )
                            # Will fail because orchestrator is mocked, but auth passes
                            assert response.status_code != 401

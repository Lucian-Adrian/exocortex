"""
Unit tests for n8n integration helpers.
"""

import pytest

from exo.integrations.n8n import (
    format_n8n_response,
    validate_n8n_webhook,
    format_ingest_response,
    format_query_response,
    format_error_response,
)


class TestFormatN8nResponse:
    """Tests for format_n8n_response function."""

    def test_format_success_response(self) -> None:
        """Formats successful response correctly."""
        data = {"answer": "Hello world"}
        result = format_n8n_response(data, success=True)

        assert result["success"] is True
        assert result["data"] == data
        assert "timestamp" in result
        assert result["metadata"] == {}

    def test_format_error_response(self) -> None:
        """Formats error response correctly."""
        data = {"code": "ERROR"}
        result = format_n8n_response(data, success=False, error="Something went wrong")

        assert result["success"] is False
        assert result["error"] == "Something went wrong"

    def test_format_list_response(self) -> None:
        """Includes count for list data."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = format_n8n_response(data, success=True)

        assert result["count"] == 3
        assert result["data"] == data

    def test_format_with_metadata(self) -> None:
        """Includes custom metadata."""
        data = {"value": 42}
        metadata = {"operation": "test", "version": "1.0"}
        result = format_n8n_response(data, success=True, metadata=metadata)

        assert result["metadata"] == metadata


class TestValidateN8nWebhook:
    """Tests for validate_n8n_webhook function."""

    def test_valid_payload(self) -> None:
        """Validates correct payload."""
        payload = {"text": "Hello", "source_type": "markdown"}
        is_valid, error = validate_n8n_webhook(payload, required_fields=["text"])

        assert is_valid is True
        assert error is None

    def test_missing_required_field(self) -> None:
        """Rejects payload missing required field."""
        payload = {"source_type": "markdown"}
        is_valid, error = validate_n8n_webhook(payload, required_fields=["text"])

        assert is_valid is False
        assert "Missing required field: text" in error

    def test_empty_required_field(self) -> None:
        """Rejects payload with empty required field."""
        payload = {"text": "", "source_type": "markdown"}
        is_valid, error = validate_n8n_webhook(payload, required_fields=["text"])

        assert is_valid is False
        assert "cannot be empty" in error

    def test_null_required_field(self) -> None:
        """Rejects payload with null required field."""
        payload = {"text": None}
        is_valid, error = validate_n8n_webhook(payload, required_fields=["text"])

        assert is_valid is False
        assert "cannot be null" in error

    def test_non_dict_payload(self) -> None:
        """Rejects non-dict payload."""
        is_valid, error = validate_n8n_webhook("not a dict")  # type: ignore

        assert is_valid is False
        assert "must be a JSON object" in error

    def test_no_required_fields(self) -> None:
        """Accepts any payload when no required fields."""
        payload = {"anything": "goes"}
        is_valid, error = validate_n8n_webhook(payload)

        assert is_valid is True
        assert error is None


class TestFormatIngestResponse:
    """Tests for format_ingest_response function."""

    def test_format_ingest_response(self) -> None:
        """Formats ingest response correctly."""
        result = format_ingest_response(
            memory_id="abc123",
            summary="Test summary",
            commitment_count=2,
            entity_count=5,
        )

        assert result["success"] is True
        assert result["data"]["id"] == "abc123"
        assert result["data"]["summary"] == "Test summary"
        assert result["data"]["commitment_count"] == 2
        assert result["data"]["entity_count"] == 5
        assert result["metadata"]["operation"] == "ingest"


class TestFormatQueryResponse:
    """Tests for format_query_response function."""

    def test_format_query_response(self) -> None:
        """Formats query response correctly."""
        result = format_query_response(
            answer="The answer is 42",
            source_count=3,
            confidence=0.95,
            commitments=[{"to": "John", "what": "send email"}],
        )

        assert result["success"] is True
        assert result["data"]["answer"] == "The answer is 42"
        assert result["data"]["source_count"] == 3
        assert result["data"]["confidence"] == 0.95
        assert len(result["data"]["commitments"]) == 1
        assert result["metadata"]["operation"] == "query"


class TestFormatErrorResponse:
    """Tests for format_error_response function."""

    def test_format_error_response(self) -> None:
        """Formats error response correctly."""
        result = format_error_response(
            error_code="PARSE_ERROR",
            message="Failed to parse content",
            details={"line": 42},
        )

        assert result["success"] is False
        assert result["error"] == "Failed to parse content"
        assert result["data"]["code"] == "PARSE_ERROR"
        assert result["data"]["message"] == "Failed to parse content"
        assert result["data"]["details"]["line"] == 42

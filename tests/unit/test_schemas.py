"""
Unit tests for Exo schemas.

Tests all Pydantic models for:
- Valid construction
- Validation constraints
- Serialization/deserialization
- Default values
"""

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from exo.schemas import (
    Commitment,
    CommitmentStatus,
    EnrichedContent,
    Entity,
    ErrorCode,
    ExoError,
    Intent,
    Memory,
    ParsedContent,
    QueryRequest,
    QueryResponse,
    RawContent,
    Source,
    SourceType,
)


# =============================================================================
# Task 1.1: Content Models
# =============================================================================


class TestSourceType:
    """Tests for SourceType enum."""

    def test_all_source_types_exist(self) -> None:
        """All expected source types are defined."""
        assert SourceType.AUDIO == "audio"
        assert SourceType.TELEGRAM == "telegram"
        assert SourceType.SLACK == "slack"
        assert SourceType.MARKDOWN == "markdown"
        assert SourceType.CODE == "code"

    def test_source_type_is_string(self) -> None:
        """SourceType values are strings for JSON serialization."""
        assert isinstance(SourceType.AUDIO.value, str)


class TestRawContent:
    """Tests for RawContent model."""

    def test_valid_raw_content(self) -> None:
        """RawContent can be created with valid data."""
        content = RawContent(
            text="Meeting with John",
            source_type=SourceType.AUDIO,
            source_file="meeting.json",
            metadata={"duration": 3600},
        )
        assert content.text == "Meeting with John"
        assert content.source_type == SourceType.AUDIO
        assert content.source_file == "meeting.json"
        assert content.metadata == {"duration": 3600}

    def test_raw_content_defaults(self) -> None:
        """RawContent has sensible defaults."""
        content = RawContent(text="Test", source_type=SourceType.MARKDOWN)
        assert content.source_file is None
        assert content.metadata == {}
        assert isinstance(content.timestamp, datetime)

    def test_raw_content_empty_text_rejected(self) -> None:
        """RawContent rejects empty text."""
        with pytest.raises(ValidationError) as exc_info:
            RawContent(text="", source_type=SourceType.AUDIO)
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_raw_content_string_source_type(self) -> None:
        """RawContent accepts string for source_type."""
        content = RawContent(text="Test", source_type="audio")
        assert content.source_type == SourceType.AUDIO

    def test_raw_content_invalid_source_type(self) -> None:
        """RawContent rejects invalid source_type."""
        with pytest.raises(ValidationError) as exc_info:
            RawContent(text="Test", source_type="invalid")
        assert "Input should be" in str(exc_info.value)


class TestParsedContent:
    """Tests for ParsedContent model."""

    def test_valid_parsed_content(self) -> None:
        """ParsedContent can be created with valid data."""
        raw = RawContent(text="Test", source_type=SourceType.AUDIO)
        parsed = ParsedContent(
            raw=raw,
            chunks=["Test"],
            structure={"speakers": ["John"]},
            content_hash="a" * 64,
        )
        assert parsed.raw == raw
        assert parsed.chunks == ["Test"]
        assert parsed.structure == {"speakers": ["John"]}
        assert len(parsed.content_hash) == 64

    def test_parsed_content_hash_validation(self) -> None:
        """ParsedContent validates hash length."""
        raw = RawContent(text="Test", source_type=SourceType.AUDIO)
        with pytest.raises(ValidationError) as exc_info:
            ParsedContent(raw=raw, chunks=["Test"], structure={}, content_hash="short")
        assert "at least 64 characters" in str(exc_info.value)


# =============================================================================
# Task 1.2: Enriched Models
# =============================================================================


class TestIntent:
    """Tests for Intent enum."""

    def test_all_intents_exist(self) -> None:
        """All expected intents are defined."""
        assert Intent.DECISION == "decision"
        assert Intent.COMMITMENT == "commitment"
        assert Intent.QUESTION == "question"
        assert Intent.IDEA == "idea"
        assert Intent.TASK == "task"
        assert Intent.UNCLASSIFIED == "unclassified"


class TestEntity:
    """Tests for Entity model."""

    def test_valid_entity(self) -> None:
        """Entity can be created with valid data."""
        entity = Entity(
            name="John",
            type="person",
            confidence=0.95,
            normalized="John Doe",
        )
        assert entity.name == "John"
        assert entity.type == "person"
        assert entity.confidence == 0.95
        assert entity.normalized == "John Doe"

    def test_entity_confidence_bounds(self) -> None:
        """Entity confidence must be between 0 and 1."""
        with pytest.raises(ValidationError):
            Entity(name="John", type="person", confidence=1.5)
        with pytest.raises(ValidationError):
            Entity(name="John", type="person", confidence=-0.1)

    def test_entity_normalized_optional(self) -> None:
        """Entity normalized field is optional."""
        entity = Entity(name="John", type="person", confidence=0.9)
        assert entity.normalized is None


class TestCommitment:
    """Tests for Commitment model."""

    def test_valid_commitment(self) -> None:
        """Commitment can be created with valid data."""
        commitment = Commitment(
            from_party="me",
            to_party="John",
            description="Send contract",
            due_date=datetime(2024, 12, 2),
            status=CommitmentStatus.OPEN,
        )
        assert commitment.from_party == "me"
        assert commitment.to_party == "John"
        assert commitment.description == "Send contract"
        assert commitment.due_date == datetime(2024, 12, 2)
        assert commitment.status == CommitmentStatus.OPEN

    def test_commitment_defaults(self) -> None:
        """Commitment has sensible defaults."""
        commitment = Commitment(
            from_party="me",
            to_party="John",
            description="Test",
        )
        assert commitment.due_date is None
        assert commitment.status == CommitmentStatus.OPEN

    def test_commitment_status_values(self) -> None:
        """CommitmentStatus has all expected values."""
        assert CommitmentStatus.OPEN == "open"
        assert CommitmentStatus.COMPLETE == "complete"
        assert CommitmentStatus.OVERDUE == "overdue"


class TestEnrichedContent:
    """Tests for EnrichedContent model."""

    def test_valid_enriched_content(self) -> None:
        """EnrichedContent can be created with valid data."""
        enriched = EnrichedContent(
            intents=[Intent.DECISION, Intent.COMMITMENT],
            confidence=0.92,
            entities=[Entity(name="John", type="person", confidence=0.95)],
            commitments=[
                Commitment(from_party="me", to_party="John", description="Send doc")
            ],
            summary="Met with John, agreed on pricing.",
            topics=["pricing", "business"],
        )
        assert len(enriched.intents) == 2
        assert enriched.confidence == 0.92
        assert len(enriched.entities) == 1
        assert len(enriched.commitments) == 1
        assert enriched.summary == "Met with John, agreed on pricing."
        assert enriched.topics == ["pricing", "business"]

    def test_enriched_content_defaults(self) -> None:
        """EnrichedContent has sensible defaults."""
        enriched = EnrichedContent(
            confidence=0.8,
            summary="Test summary",
        )
        assert enriched.intents == []
        assert enriched.entities == []
        assert enriched.commitments == []
        assert enriched.topics == []

    def test_enriched_content_summary_max_length(self) -> None:
        """EnrichedContent summary has max length."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedContent(
                confidence=0.8,
                summary="x" * 501,  # Over 500 char limit
            )
        assert "at most 500 characters" in str(exc_info.value)


# =============================================================================
# Task 1.3: Memory Model
# =============================================================================


class TestMemory:
    """Tests for Memory model."""

    def test_valid_memory(self) -> None:
        """Memory can be created with valid data."""
        memory = Memory(
            content="Meeting with John about pricing.",
            summary="Pricing discussion with John.",
            intents=["decision", "commitment"],
            entities={"people": ["John"]},
            commitments=[{"from": "me", "to": "John", "what": "send contract"}],
            source_type=SourceType.AUDIO,
            source_file="meeting.json",
        )
        assert memory.content == "Meeting with John about pricing."
        assert memory.summary == "Pricing discussion with John."
        assert memory.intents == ["decision", "commitment"]
        assert memory.entities == {"people": ["John"]}
        assert memory.source_type == SourceType.AUDIO
        assert memory.id is None  # Before DB insert

    def test_memory_with_id(self) -> None:
        """Memory can have a UUID id."""
        uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        memory = Memory(
            id=uuid,
            content="Test",
            summary="Test summary",
            source_type=SourceType.MARKDOWN,
        )
        assert memory.id == uuid

    def test_memory_with_embedding(self) -> None:
        """Memory can store embedding vector."""
        embedding = [0.1] * 768
        memory = Memory(
            content="Test",
            summary="Test summary",
            source_type=SourceType.AUDIO,
            embedding=embedding,
        )
        assert memory.embedding == embedding
        assert len(memory.embedding) == 768

    def test_memory_defaults(self) -> None:
        """Memory has sensible defaults."""
        memory = Memory(
            content="Test",
            summary="Summary",
            source_type=SourceType.AUDIO,
        )
        assert memory.id is None
        assert memory.intents == []
        assert memory.entities == {}
        assert memory.commitments == []
        assert memory.embedding is None
        assert memory.source_file is None
        assert isinstance(memory.created_at, datetime)


# =============================================================================
# Task 1.4: Query Models
# =============================================================================


class TestQueryRequest:
    """Tests for QueryRequest model."""

    def test_valid_query_request(self) -> None:
        """QueryRequest can be created with valid data."""
        request = QueryRequest(
            question="What did I promise John?",
            top_k=5,
            similarity_threshold=0.8,
            filters={"source_type": "audio"},
        )
        assert request.question == "What did I promise John?"
        assert request.top_k == 5
        assert request.similarity_threshold == 0.8
        assert request.filters == {"source_type": "audio"}

    def test_query_request_defaults(self) -> None:
        """QueryRequest has sensible defaults."""
        request = QueryRequest(question="Test question?")
        assert request.top_k == 10
        assert request.similarity_threshold == 0.7
        assert request.filters == {}

    def test_query_request_top_k_bounds(self) -> None:
        """QueryRequest top_k has bounds."""
        with pytest.raises(ValidationError):
            QueryRequest(question="Test", top_k=0)
        with pytest.raises(ValidationError):
            QueryRequest(question="Test", top_k=51)

    def test_query_request_threshold_bounds(self) -> None:
        """QueryRequest similarity_threshold has bounds."""
        with pytest.raises(ValidationError):
            QueryRequest(question="Test", similarity_threshold=-0.1)
        with pytest.raises(ValidationError):
            QueryRequest(question="Test", similarity_threshold=1.1)


class TestSource:
    """Tests for Source model."""

    def test_valid_source(self) -> None:
        """Source can be created with valid data."""
        source = Source(
            memory_id="550e8400-e29b-41d4-a716-446655440000",
            content_preview="Meeting with John...",
            similarity=0.92,
            source_file="meeting.json",
        )
        assert source.memory_id == "550e8400-e29b-41d4-a716-446655440000"
        assert source.content_preview == "Meeting with John..."
        assert source.similarity == 0.92
        assert source.source_file == "meeting.json"

    def test_source_similarity_bounds(self) -> None:
        """Source similarity has bounds."""
        with pytest.raises(ValidationError):
            Source(
                memory_id="test",
                content_preview="Test",
                similarity=1.5,
            )


class TestQueryResponse:
    """Tests for QueryResponse model."""

    def test_valid_query_response(self) -> None:
        """QueryResponse can be created with valid data."""
        response = QueryResponse(
            answer="You promised to send the contract.",
            sources=[
                Source(
                    memory_id="test-id",
                    content_preview="Meeting...",
                    similarity=0.9,
                )
            ],
            commitments=[{"to": "John", "what": "send contract"}],
            confidence=0.91,
        )
        assert response.answer == "You promised to send the contract."
        assert len(response.sources) == 1
        assert len(response.commitments) == 1
        assert response.confidence == 0.91

    def test_query_response_defaults(self) -> None:
        """QueryResponse has sensible defaults."""
        response = QueryResponse(
            answer="Test answer",
            confidence=0.8,
        )
        assert response.sources == []
        assert response.commitments == []


# =============================================================================
# Task 1.5: Error Model
# =============================================================================


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_all_error_codes_exist(self) -> None:
        """All expected error codes are defined."""
        assert ErrorCode.PARSE_ERROR == "PARSE_ERROR"
        assert ErrorCode.ENRICH_ERROR == "ENRICH_ERROR"
        assert ErrorCode.EMBED_ERROR == "EMBED_ERROR"
        assert ErrorCode.STORE_ERROR == "STORE_ERROR"
        assert ErrorCode.QUERY_ERROR == "QUERY_ERROR"
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.AI_UNAVAILABLE == "AI_UNAVAILABLE"


class TestExoError:
    """Tests for ExoError model."""

    def test_valid_exo_error(self) -> None:
        """ExoError can be created with valid data."""
        error = ExoError(
            code=ErrorCode.ENRICH_ERROR,
            message="Gemini API failed",
            details={"status_code": 500},
            recoverable=True,
        )
        assert error.code == ErrorCode.ENRICH_ERROR
        assert error.message == "Gemini API failed"
        assert error.details == {"status_code": 500}
        assert error.recoverable is True

    def test_exo_error_defaults(self) -> None:
        """ExoError has sensible defaults."""
        error = ExoError(
            code=ErrorCode.PARSE_ERROR,
            message="Parse failed",
        )
        assert error.details == {}
        assert error.recoverable is True

    def test_exo_error_str(self) -> None:
        """ExoError has readable string representation."""
        error = ExoError(
            code=ErrorCode.ENRICH_ERROR,
            message="API timeout",
        )
        assert str(error) == "[ENRICH_ERROR] API timeout"

    def test_exo_error_repr(self) -> None:
        """ExoError has debug representation."""
        error = ExoError(
            code=ErrorCode.ENRICH_ERROR,
            message="API timeout",
            recoverable=False,
        )
        assert "ExoError" in repr(error)
        assert "ENRICH_ERROR" in repr(error)


# =============================================================================
# Task 1.6: Schema Exports
# =============================================================================


class TestSchemaExports:
    """Tests for schema module exports."""

    def test_all_exports_available(self) -> None:
        """All expected exports are available from exo.schemas."""
        from exo import schemas

        # Content
        assert hasattr(schemas, "SourceType")
        assert hasattr(schemas, "RawContent")
        assert hasattr(schemas, "ParsedContent")

        # Enriched
        assert hasattr(schemas, "Intent")
        assert hasattr(schemas, "Entity")
        assert hasattr(schemas, "Commitment")
        assert hasattr(schemas, "CommitmentStatus")
        assert hasattr(schemas, "EnrichedContent")

        # Memory
        assert hasattr(schemas, "Memory")

        # Query
        assert hasattr(schemas, "QueryRequest")
        assert hasattr(schemas, "Source")
        assert hasattr(schemas, "QueryResponse")

        # Errors
        assert hasattr(schemas, "ErrorCode")
        assert hasattr(schemas, "ExoError")

    def test_direct_import(self) -> None:
        """Models can be imported directly from exo.schemas."""
        from exo.schemas import ExoError, Memory, QueryResponse, RawContent

        # Just verify they're the right types
        assert RawContent.__name__ == "RawContent"
        assert Memory.__name__ == "Memory"
        assert QueryResponse.__name__ == "QueryResponse"
        assert ExoError.__name__ == "ExoError"

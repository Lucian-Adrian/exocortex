"""
Unit tests for content parsers.

Tests parser implementations and factory.
"""

import json
import pytest
from exo.parsers import (
    Parser,
    TranscriptParser,
    TelegramParser,
    MarkdownParser,
    get_parser,
)
from exo.schemas.content import RawContent, ParsedContent, SourceType


class TestParserABC:
    """Tests for Parser abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        """Parser ABC cannot be instantiated."""
        with pytest.raises(TypeError, match="abstract"):
            Parser()  # type: ignore

    def test_subclass_must_implement_supported_types(self) -> None:
        """Subclass must implement supported_types property."""
        class IncompleteParser(Parser):
            def parse(self, content: RawContent) -> ParsedContent:
                pass
            def validate(self, content: RawContent) -> bool:
                return True

        with pytest.raises(TypeError, match="abstract"):
            IncompleteParser()  # type: ignore

    def test_subclass_must_implement_parse(self) -> None:
        """Subclass must implement parse method."""
        class IncompleteParser(Parser):
            @property
            def supported_types(self) -> list[str]:
                return ["test"]
            def validate(self, content: RawContent) -> bool:
                return True

        with pytest.raises(TypeError, match="abstract"):
            IncompleteParser()  # type: ignore


class TestTranscriptParser:
    """Tests for TranscriptParser."""

    def test_supported_types(self) -> None:
        """TranscriptParser supports audio source type."""
        parser = TranscriptParser()
        assert SourceType.AUDIO in parser.supported_types

    def test_validate_json_with_segments(self) -> None:
        """Validates JSON with segments array."""
        parser = TranscriptParser()
        content = RawContent(
            text=json.dumps({
                "segments": [
                    {"speaker": "Alice", "text": "Hello", "start": 0.0, "end": 1.5}
                ]
            }),
            source_type=SourceType.AUDIO,
        )
        assert parser.validate(content) is True

    def test_validate_plain_text(self) -> None:
        """Validates plain text transcripts."""
        parser = TranscriptParser()
        content = RawContent(
            text="This is a plain text transcript.",
            source_type=SourceType.AUDIO,
        )
        assert parser.validate(content) is True

    def test_validate_rejects_whitespace(self) -> None:
        """Rejects whitespace-only content."""
        parser = TranscriptParser()
        content = RawContent(text="   ", source_type=SourceType.AUDIO)
        assert parser.validate(content) is False

    def test_parse_json_segments(self) -> None:
        """Parses JSON with speaker segments."""
        parser = TranscriptParser()
        content = RawContent(
            text=json.dumps({
                "segments": [
                    {"speaker": "Alice", "text": "Hello", "start": 0.0, "end": 1.5},
                    {"speaker": "Bob", "text": "Hi there", "start": 1.5, "end": 3.0},
                ],
                "metadata": {"duration": 3.0}
            }),
            source_type=SourceType.AUDIO,
        )
        
        result = parser.parse(content)
        
        assert isinstance(result, ParsedContent)
        assert len(result.chunks) == 2
        assert "Alice: Hello" in result.chunks[0]
        assert "Bob: Hi there" in result.chunks[1]
        assert set(result.structure["speakers"]) == {"Alice", "Bob"}
        assert result.structure["segment_count"] == 2
        assert result.content_hash  # Hash generated

    def test_parse_plain_text(self) -> None:
        """Parses plain text into paragraph chunks."""
        parser = TranscriptParser()
        content = RawContent(
            text="First paragraph.\n\nSecond paragraph.",
            source_type=SourceType.AUDIO,
        )
        
        result = parser.parse(content)
        
        assert len(result.chunks) == 2
        assert result.chunks[0] == "First paragraph."
        assert result.chunks[1] == "Second paragraph."


class TestTelegramParser:
    """Tests for TelegramParser."""

    def test_supported_types(self) -> None:
        """TelegramParser supports telegram source type."""
        parser = TelegramParser()
        assert SourceType.TELEGRAM in parser.supported_types

    def test_validate_telegram_export(self) -> None:
        """Validates Telegram export format."""
        parser = TelegramParser()
        content = RawContent(
            text=json.dumps({
                "name": "Test Chat",
                "type": "personal_chat",
                "messages": []
            }),
            source_type=SourceType.TELEGRAM,
        )
        assert parser.validate(content) is True

    def test_validate_rejects_invalid_json(self) -> None:
        """Rejects invalid JSON."""
        parser = TelegramParser()
        content = RawContent(text="not json", source_type=SourceType.TELEGRAM)
        assert parser.validate(content) is False

    def test_validate_rejects_json_without_messages(self) -> None:
        """Rejects JSON without messages array."""
        parser = TelegramParser()
        content = RawContent(
            text=json.dumps({"name": "Test"}),
            source_type=SourceType.TELEGRAM,
        )
        assert parser.validate(content) is False

    def test_parse_telegram_messages(self) -> None:
        """Parses Telegram messages into chunks."""
        parser = TelegramParser()
        content = RawContent(
            text=json.dumps({
                "name": "Test Chat",
                "type": "personal_chat",
                "messages": [
                    {"type": "message", "from": "Alice", "text": "Hello!", "date": "2024-01-01T10:00:00"},
                    {"type": "message", "from": "Bob", "text": "Hi!", "date": "2024-01-01T10:01:00"},
                ]
            }),
            source_type=SourceType.TELEGRAM,
        )
        
        result = parser.parse(content)
        
        assert len(result.chunks) == 2
        assert "Alice: Hello!" in result.chunks[0]
        assert "Bob: Hi!" in result.chunks[1]
        assert set(result.structure["participants"]) == {"Alice", "Bob"}
        assert result.structure["message_count"] == 2

    def test_parse_skips_service_messages(self) -> None:
        """Skips non-message types."""
        parser = TelegramParser()
        content = RawContent(
            text=json.dumps({
                "name": "Test",
                "messages": [
                    {"type": "service", "action": "joined"},
                    {"type": "message", "from": "Alice", "text": "Hello!"},
                ]
            }),
            source_type=SourceType.TELEGRAM,
        )
        
        result = parser.parse(content)
        
        assert len(result.chunks) == 1
        assert "Alice: Hello!" in result.chunks[0]


class TestMarkdownParser:
    """Tests for MarkdownParser."""

    def test_supported_types(self) -> None:
        """MarkdownParser supports markdown source type."""
        parser = MarkdownParser()
        assert SourceType.MARKDOWN in parser.supported_types

    def test_validate_any_text(self) -> None:
        """Validates any non-empty text."""
        parser = MarkdownParser()
        content = RawContent(text="Some text", source_type=SourceType.MARKDOWN)
        assert parser.validate(content) is True

    def test_validate_rejects_whitespace(self) -> None:
        """Rejects whitespace-only content."""
        parser = MarkdownParser()
        content = RawContent(text="   ", source_type=SourceType.MARKDOWN)
        assert parser.validate(content) is False

    def test_parse_with_headers(self) -> None:
        """Parses markdown with headers into sections."""
        parser = MarkdownParser()
        content = RawContent(
            text="# Title\n\nIntro text.\n\n## Section 1\n\nContent 1.\n\n## Section 2\n\nContent 2.",
            source_type=SourceType.MARKDOWN,
        )
        
        result = parser.parse(content)
        
        # Should have 3 chunks: intro, section 1, section 2
        assert len(result.chunks) >= 2
        assert len(result.structure["headers"]) == 3
        assert result.structure["headers"][0]["title"] == "Title"
        assert result.structure["headers"][0]["level"] == 1

    def test_parse_without_headers(self) -> None:
        """Parses markdown without headers as single chunk."""
        parser = MarkdownParser()
        content = RawContent(
            text="Just some plain text without any headers.",
            source_type=SourceType.MARKDOWN,
        )
        
        result = parser.parse(content)
        
        assert len(result.chunks) == 1
        assert result.structure["headers"] == []

    def test_parse_nested_headers(self) -> None:
        """Builds correct header tree for nested headers."""
        parser = MarkdownParser()
        content = RawContent(
            text="# Main\n\n## Sub 1\n\n### Sub 1.1\n\n## Sub 2",
            source_type=SourceType.MARKDOWN,
        )
        
        result = parser.parse(content)
        
        tree = result.structure["header_tree"]
        assert len(tree) == 1  # One top-level header
        assert tree[0]["title"] == "Main"
        assert len(tree[0]["children"]) == 2  # Two sub-headers


class TestParserFactory:
    """Tests for parser factory."""

    def test_get_parser_audio(self) -> None:
        """Returns TranscriptParser for audio."""
        parser = get_parser(SourceType.AUDIO)
        assert isinstance(parser, TranscriptParser)

    def test_get_parser_telegram(self) -> None:
        """Returns TelegramParser for telegram."""
        parser = get_parser(SourceType.TELEGRAM)
        assert isinstance(parser, TelegramParser)

    def test_get_parser_markdown(self) -> None:
        """Returns MarkdownParser for markdown."""
        parser = get_parser(SourceType.MARKDOWN)
        assert isinstance(parser, MarkdownParser)

    def test_get_parser_string_type(self) -> None:
        """Accepts string source type."""
        parser = get_parser("audio")
        assert isinstance(parser, TranscriptParser)

    def test_get_parser_code_fallback(self) -> None:
        """Falls back to MarkdownParser for code type."""
        parser = get_parser(SourceType.CODE)
        assert isinstance(parser, MarkdownParser)

    def test_get_parser_unknown_fallback(self) -> None:
        """Falls back to MarkdownParser for unknown type."""
        parser = get_parser("unknown_type")
        assert isinstance(parser, MarkdownParser)

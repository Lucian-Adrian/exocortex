"""
Parser factory.

Returns appropriate parser based on SourceType.
"""

from exo.parsers.base import Parser
from exo.parsers.transcript import TranscriptParser
from exo.parsers.telegram import TelegramParser
from exo.parsers.markdown import MarkdownParser
from exo.schemas.content import SourceType


# Parser registry: source_type -> parser instance
_PARSERS: dict[str, Parser] = {
    SourceType.AUDIO: TranscriptParser(),
    SourceType.TELEGRAM: TelegramParser(),
    SourceType.SLACK: TelegramParser(),  # Slack uses same chat parser
    SourceType.MARKDOWN: MarkdownParser(),
    SourceType.CODE: MarkdownParser(),  # Code uses markdown-like parser
}


def get_parser(source_type: str | SourceType) -> Parser:
    """
    Get parser for a given source type.
    
    Args:
        source_type: The source type (SourceType enum or string).
        
    Returns:
        Parser instance for the source type.
        
    Raises:
        ValueError: If no parser exists for the source type.
    """
    # Normalize to string
    if isinstance(source_type, SourceType):
        type_str = source_type.value
    else:
        type_str = source_type

    # Check registry
    parser = _PARSERS.get(type_str)
    if parser:
        return parser

    # Fallback: try to match against any parser's supported types
    for parser in _PARSERS.values():
        if type_str in parser.supported_types:
            return parser

    # Default to markdown parser for unknown types (most flexible)
    # Try markdown as fallback
    return _PARSERS[SourceType.MARKDOWN]


def register_parser(source_type: str | SourceType, parser: Parser) -> None:
    """
    Register a custom parser for a source type.
    
    Args:
        source_type: The source type to register for.
        parser: Parser instance to register.
    """
    type_str = source_type.value if isinstance(source_type, SourceType) else source_type
    _PARSERS[type_str] = parser

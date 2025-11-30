"""
Abstract base class for content parsers.

All parsers must implement the Parser interface.
"""

from abc import ABC, abstractmethod

from exo.schemas.content import RawContent, ParsedContent


class Parser(ABC):
    """
    Abstract base for content parsers.
    
    Each parser handles a specific source type (audio transcripts,
    chat exports, markdown files, etc.) and converts RawContent
    into ParsedContent with structured chunks.
    """

    @property
    @abstractmethod
    def supported_types(self) -> list[str]:
        """Return list of supported source types."""
        ...

    @abstractmethod
    def parse(self, content: RawContent) -> ParsedContent:
        """
        Parse raw content into structured format.
        
        Args:
            content: Raw content with text and metadata.
            
        Returns:
            ParsedContent with chunks, structure, and hash.
            
        Raises:
            ValueError: If content cannot be parsed.
        """
        ...

    @abstractmethod
    def validate(self, content: RawContent) -> bool:
        """
        Validate content can be parsed.
        
        Args:
            content: Raw content to validate.
            
        Returns:
            True if content is valid for this parser.
        """
        ...

"""
Parse pipeline step.

Converts RawContent to ParsedContent using appropriate parser.
"""

from exo.parsers.factory import get_parser
from exo.schemas.content import RawContent, ParsedContent
from exo.schemas.errors import ExoError, ErrorCode


async def parse(content: RawContent) -> ParsedContent | ExoError:
    """
    Parse raw content into structured format.
    
    Uses parser factory to select appropriate parser based on
    source_type, then parses the content into chunks with structure.
    
    Args:
        content: Raw content with text and metadata.
        
    Returns:
        ParsedContent with chunks and structure, or ExoError on failure.
    """
    try:
        parser = get_parser(content.source_type)
        
        if not parser.validate(content):
            return ExoError(
                code=ErrorCode.PARSE_ERROR,
                message=f"Content validation failed for type: {content.source_type}",
                details={"source_type": str(content.source_type)},
                recoverable=False,
            )
        
        return parser.parse(content)
        
    except ValueError as e:
        return ExoError(
            code=ErrorCode.PARSE_ERROR,
            message=str(e),
            details={"source_type": str(content.source_type)},
            recoverable=False,
        )
    except Exception as e:
        return ExoError(
            code=ErrorCode.PARSE_ERROR,
            message=f"Unexpected parse error: {e}",
            details={
                "source_type": str(content.source_type),
                "error_type": type(e).__name__,
            },
            recoverable=True,
        )

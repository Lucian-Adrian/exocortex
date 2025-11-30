"""
Parser for Markdown documents.

Extracts structure from headers and chunks content by sections.
"""

import hashlib
import re
from typing import Any

from exo.parsers.base import Parser
from exo.schemas.content import RawContent, ParsedContent, SourceType


class MarkdownParser(Parser):
    """
    Parser for Markdown documents.
    
    Extracts headers as structure and chunks by sections.
    Supports standard Markdown headers (# ## ### etc.)
    """

    # Pattern for markdown headers
    HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    @property
    def supported_types(self) -> list[str]:
        """Return supported source types."""
        return [SourceType.MARKDOWN, SourceType.CODE]

    def validate(self, content: RawContent) -> bool:
        """Validate content can be parsed as Markdown."""
        if not content.text or not content.text.strip():
            return False
        # Any non-empty text is valid markdown
        return True

    def parse(self, content: RawContent) -> ParsedContent:
        """Parse Markdown into sections by headers."""
        if not self.validate(content):
            raise ValueError("Invalid Markdown content")

        text = content.text
        chunks: list[str] = []
        structure: dict[str, Any] = {
            "headers": [],
            "header_tree": [],
        }

        # Find all headers with their positions
        headers = list(self.HEADER_PATTERN.finditer(text))
        
        if not headers:
            # No headers - treat entire content as single chunk
            chunks.append(text.strip())
        else:
            # Extract header structure
            for match in headers:
                level = len(match.group(1))  # Number of # symbols
                title = match.group(2).strip()
                structure["headers"].append({
                    "level": level,
                    "title": title,
                    "position": match.start(),
                })

            # Build header tree (for nested structure)
            structure["header_tree"] = self._build_header_tree(structure["headers"])

            # Split content by headers into chunks
            for i, match in enumerate(headers):
                start = match.start()
                end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
                section = text[start:end].strip()
                if section:
                    chunks.append(section)

            # Include any content before first header
            first_header_pos = headers[0].start() if headers else len(text)
            preamble = text[:first_header_pos].strip()
            if preamble:
                chunks.insert(0, preamble)

        # Generate content hash
        content_hash = hashlib.sha256(content.text.encode("utf-8")).hexdigest()

        return ParsedContent(
            raw=content,
            chunks=chunks,
            structure=structure,
            content_hash=content_hash,
        )

    def _build_header_tree(self, headers: list[dict]) -> list[dict]:
        """
        Build a nested tree structure from flat header list.
        
        Args:
            headers: List of {level, title, position} dicts.
            
        Returns:
            Nested list representing header hierarchy.
        """
        if not headers:
            return []

        tree: list[dict] = []
        stack: list[dict] = []

        for header in headers:
            node = {
                "title": header["title"],
                "level": header["level"],
                "children": [],
            }

            # Pop items from stack until we find a parent (lower level)
            while stack and stack[-1]["level"] >= header["level"]:
                stack.pop()

            if stack:
                # Add as child of the top of stack
                stack[-1]["children"].append(node)
            else:
                # Top-level header
                tree.append(node)

            stack.append(node)

        return tree

"""
Parser for Telegram JSON exports.

Handles Telegram exported chat history with participants,
messages, and threads.
"""

import hashlib
import json
from typing import Any

from exo.parsers.base import Parser
from exo.schemas.content import RawContent, ParsedContent, SourceType


class TelegramParser(Parser):
    """
    Parser for Telegram JSON export format.
    
    Expected format (Telegram export):
    {
        "name": "Chat Name",
        "type": "personal_chat" | "private_group" | ...,
        "messages": [
            {
                "id": 1,
                "type": "message",
                "from": "User Name",
                "text": "Hello!",
                "date": "2024-01-01T10:00:00"
            }
        ]
    }
    """

    @property
    def supported_types(self) -> list[str]:
        """Return supported source types."""
        return [SourceType.TELEGRAM, SourceType.SLACK]

    def validate(self, content: RawContent) -> bool:
        """Validate content can be parsed as Telegram export."""
        if not content.text or not content.text.strip():
            return False

        try:
            data = json.loads(content.text)
            # Must have messages array (Telegram export format)
            return isinstance(data, dict) and "messages" in data
        except json.JSONDecodeError:
            return False

    def parse(self, content: RawContent) -> ParsedContent:
        """Parse Telegram export into message chunks."""
        if not self.validate(content):
            raise ValueError("Invalid Telegram export content")

        data = json.loads(content.text)
        messages = data.get("messages", [])
        
        chunks: list[str] = []
        structure: dict[str, Any] = {
            "chat_name": data.get("name", "Unknown"),
            "chat_type": data.get("type", "unknown"),
            "participants": set(),
            "message_count": 0,
        }

        for msg in messages:
            # Skip non-message types (service messages, etc.)
            if msg.get("type") != "message":
                continue

            sender = msg.get("from", "Unknown")
            text = msg.get("text", "")
            
            # Handle complex text (with formatting entities)
            if isinstance(text, list):
                # Telegram stores formatted text as array
                text_parts = []
                for part in text:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict):
                        text_parts.append(part.get("text", ""))
                text = "".join(text_parts)

            if not text or not text.strip():
                continue

            chunks.append(f"{sender}: {text.strip()}")
            structure["participants"].add(sender)
            structure["message_count"] += 1

        # Convert participants set to list for JSON serialization
        structure["participants"] = list(structure["participants"])

        # Extract date range
        if messages:
            dates = [
                msg.get("date") for msg in messages 
                if msg.get("date") and msg.get("type") == "message"
            ]
            if dates:
                structure["date_range"] = {
                    "start": min(dates),
                    "end": max(dates),
                }

        # Generate content hash
        content_hash = hashlib.sha256(content.text.encode("utf-8")).hexdigest()

        return ParsedContent(
            raw=content,
            chunks=chunks,
            structure=structure,
            content_hash=content_hash,
        )

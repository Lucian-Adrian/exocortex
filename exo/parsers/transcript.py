"""
Parser for audio transcripts from audio toolkit.

Handles JSON format from audio processing pipeline with
speaker segments and timestamps.
"""

import hashlib
import json
from typing import Any

from exo.parsers.base import Parser
from exo.schemas.content import RawContent, ParsedContent, SourceType


class TranscriptParser(Parser):
    """
    Parser for audio toolkit JSON transcript format.
    
    Expected format:
    {
        "segments": [
            {
                "speaker": "Speaker 1",
                "text": "Hello world",
                "start": 0.0,
                "end": 2.5
            }
        ],
        "metadata": {...}
    }
    
    Or plain text format (just the transcript text).
    """

    @property
    def supported_types(self) -> list[str]:
        """Return supported source types."""
        return [SourceType.AUDIO]

    def validate(self, content: RawContent) -> bool:
        """Validate content can be parsed as transcript."""
        if not content.text or not content.text.strip():
            return False
        
        # Accept JSON with segments or plain text
        if content.text.strip().startswith("{"):
            try:
                data = json.loads(content.text)
                # Must have either segments array or be parseable as transcript
                return isinstance(data, dict)
            except json.JSONDecodeError:
                return False
        
        # Plain text is always valid
        return True

    def parse(self, content: RawContent) -> ParsedContent:
        """Parse transcript into chunks by speaker segments."""
        if not self.validate(content):
            raise ValueError("Invalid transcript content")

        text = content.text.strip()
        chunks: list[str] = []
        structure: dict[str, Any] = {}

        if text.startswith("{"):
            # JSON format
            data = json.loads(text)
            segments = data.get("segments", [])
            
            if segments:
                # Extract speaker segments as chunks
                speakers = set()
                for segment in segments:
                    speaker = segment.get("speaker", "Unknown")
                    text_content = segment.get("text", "").strip()
                    if text_content:
                        chunks.append(f"{speaker}: {text_content}")
                        speakers.add(speaker)
                
                structure["speakers"] = list(speakers)
                structure["segment_count"] = len(segments)
                
                # Extract timestamps if present
                if segments and "start" in segments[0]:
                    structure["start_time"] = segments[0].get("start")
                    structure["end_time"] = segments[-1].get("end")
            else:
                # JSON but no segments - treat as single chunk
                chunks.append(str(data.get("text", text)))
            
            structure["format"] = "json"
            structure["metadata"] = data.get("metadata", {})
        else:
            # Plain text format - split by paragraphs or lines
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if paragraphs:
                chunks = paragraphs
            else:
                chunks = [text]
            
            structure["format"] = "plain"

        # Generate content hash
        content_hash = hashlib.sha256(content.text.encode("utf-8")).hexdigest()

        return ParsedContent(
            raw=content,
            chunks=chunks,
            structure=structure,
            content_hash=content_hash,
        )

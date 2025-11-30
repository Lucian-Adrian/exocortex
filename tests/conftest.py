"""
Pytest configuration and shared fixtures for Exo tests.
"""

import os
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars() -> Generator[None, None, None]:
    """
    Mock environment variables for tests.

    Ensures tests don't require real API keys.
    """
    env_vars = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "GEMINI_API_KEY": "test-gemini-key",
    }
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def mock_supabase_client() -> MagicMock:
    """Create a mock Supabase client for testing."""
    client = MagicMock()
    client.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "test-uuid"}]
    )
    return client


@pytest.fixture
def sample_raw_content() -> dict:
    """Sample raw content for testing."""
    return {
        "text": "Meeting with John. We agreed on $99/month pricing.",
        "source_type": "audio",
        "source_file": "meeting_2024-11-30.json",
        "metadata": {"duration": 1234},
    }


@pytest.fixture
def sample_enriched_data() -> dict:
    """Sample enriched content data for testing."""
    return {
        "intents": ["decision", "commitment"],
        "confidence": 0.92,
        "entities": [
            {"name": "John", "type": "person", "confidence": 0.95, "normalized": "John Doe"},
            {"name": "$99/month", "type": "amount", "confidence": 0.88, "normalized": None},
        ],
        "commitments": [
            {
                "from_party": "me",
                "to_party": "John",
                "description": "agreed on pricing",
                "due_date": None,
                "status": "open",
            }
        ],
        "summary": "Pricing decision: $99/month with John.",
        "topics": ["pricing", "business"],
    }

"""
Unit tests for database layer.

Tests query functions using mocked Supabase client.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from exo.db.queries import (
    get_commitments,
    insert_memory,
    log_error,
    search_semantic,
)
from exo.schemas.memory import Memory, SourceType


@pytest.mark.asyncio
async def test_insert_memory(mock_supabase_client: MagicMock) -> None:
    """Test inserting a memory record."""
    memory = Memory(
        content="Test content",
        summary="Test summary",
        source_type=SourceType.AUDIO,
        content_hash="a" * 64,
    )

    # Setup mock response
    mock_response = MagicMock()
    mock_response.data = [{"id": "550e8400-e29b-41d4-a716-446655440000"}]
    mock_supabase_client.table.return_value.upsert.return_value.execute.return_value = (
        mock_response
    )

    # Execute
    memory_id = await insert_memory(mock_supabase_client, memory)

    # Verify
    assert memory_id == "550e8400-e29b-41d4-a716-446655440000"
    mock_supabase_client.table.assert_called_with("memories")
    mock_supabase_client.table.return_value.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_search_semantic(mock_supabase_client: MagicMock) -> None:
    """Test semantic search RPC call."""
    embedding = [0.1] * 768
    
    # Setup mock response
    mock_response = MagicMock()
    mock_response.data = [
        {"id": "test-id", "content": "match", "similarity": 0.9}
    ]
    mock_supabase_client.rpc.return_value.execute.return_value = mock_response

    # Execute
    results = await search_semantic(
        mock_supabase_client,
        embedding,
        match_threshold=0.8,
        match_count=5,
        filter_source_type="audio",
    )

    # Verify
    assert len(results) == 1
    assert results[0]["content"] == "match"
    mock_supabase_client.rpc.assert_called_with(
        "match_memories",
        {
            "query_embedding": embedding,
            "match_threshold": 0.8,
            "match_count": 5,
            "filter_source_type": "audio",
        },
    )


@pytest.mark.asyncio
async def test_get_commitments(mock_supabase_client: MagicMock) -> None:
    """Test fetching commitments with filters."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.data = [{"id": "comm-id", "description": "task"}]
    
    # Mock the chain: table().select().eq().lte().order().order().execute()
    # This is tricky with mocks, so we just check the final execute
    query_mock = MagicMock()
    query_mock.execute.return_value = mock_response
    
    # We need to mock the chain return values
    mock_supabase_client.table.return_value.select.return_value = query_mock
    query_mock.eq.return_value = query_mock
    query_mock.lte.return_value = query_mock
    query_mock.order.return_value = query_mock

    # Execute
    results = await get_commitments(
        mock_supabase_client,
        status="open",
        due_before=datetime(2024, 12, 31, tzinfo=timezone.utc),
    )

    # Verify
    assert len(results) == 1
    mock_supabase_client.table.assert_called_with("commitments")
    # Verify filters were applied
    query_mock.eq.assert_called_with("status", "open")
    query_mock.lte.assert_called()


@pytest.mark.asyncio
async def test_log_error(mock_supabase_client: MagicMock) -> None:
    """Test error logging."""
    error_data = {
        "code": "TEST_ERROR",
        "message": "Something went wrong",
        "details": {"foo": "bar"},
    }

    # Execute
    await log_error(mock_supabase_client, error_data)

    # Verify
    mock_supabase_client.table.assert_called_with("_errors")
    mock_supabase_client.table.return_value.insert.assert_called_with({
        "error_code": "TEST_ERROR",
        "message": "Something went wrong",
        "details": {"foo": "bar"},
        "source": "exo",
    })

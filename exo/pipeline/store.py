"""
Store pipeline step.

Persists Memory objects to the database.
"""

from uuid import UUID

from supabase import Client

from exo.db.queries import insert_memory
from exo.schemas.memory import Memory
from exo.schemas.errors import ExoError, ErrorCode


async def store(
    memory: Memory,
    client: Client,
) -> Memory | ExoError:
    """
    Store memory in the database.
    
    Persists the Memory object to Supabase via insert_memory.
    Returns the Memory with populated ID on success.
    
    Args:
        memory: Memory object to store.
        client: Supabase client (REQUIRED - pooled connection from orchestrator).
        
    Returns:
        Memory with ID populated, or ExoError on failure.
    """
    try:
        # insert_memory returns the UUID as a string
        memory_id = await insert_memory(client, memory)
        
        # Return memory with ID from database
        return Memory(
            id=UUID(memory_id) if isinstance(memory_id, str) else memory_id,
            content=memory.content,
            intents=memory.intents,
            entities=memory.entities,
            commitments=memory.commitments,
            summary=memory.summary,
            embedding=memory.embedding,
            source_type=memory.source_type,
            source_file=memory.source_file,
            content_hash=memory.content_hash,
            created_at=memory.created_at,
        )
        
    except Exception as e:
        return ExoError(
            code=ErrorCode.STORE_ERROR,
            message=f"Store failed: {e}",
            details={"error_type": type(e).__name__},
            recoverable=True,
        )

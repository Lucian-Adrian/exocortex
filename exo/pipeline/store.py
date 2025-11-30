"""
Store pipeline step.

Persists Memory objects to the database.
"""

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
        result = await insert_memory(client, memory)
        
        if result.error:
            return ExoError(
                code=ErrorCode.STORE_ERROR,
                message=f"Database error: {result.error}",
                details={"db_error": result.error},
                recoverable=True,
            )
        
        # Return memory with ID from database
        if result.data and isinstance(result.data, list) and len(result.data) > 0:
            db_record = result.data[0]
            return Memory(
                id=db_record.get("id"),
                content=memory.content,
                intents=memory.intents,
                entities=memory.entities,
                commitments=memory.commitments,
                summary=memory.summary,
                embedding=memory.embedding,
                source_type=memory.source_type,
                source_file=memory.source_file,
                created_at=memory.created_at,
            )
        
        # Fallback if no data returned (shouldn't happen)
        return memory
        
    except Exception as e:
        return ExoError(
            code=ErrorCode.STORE_ERROR,
            message=f"Store failed: {e}",
            details={"error_type": type(e).__name__},
            recoverable=True,
        )

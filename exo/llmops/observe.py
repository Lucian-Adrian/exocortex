"""
Observability module for Exo using Langfuse.

Provides a decorator and utilities for tracing LLM operations.
Gracefully degrades to no-op when Langfuse is not installed or disabled.

Usage:
    from exo.llmops.observe import observe, trace_generation

    @observe
    def my_llm_function():
        ...

    # Or trace a specific generation
    trace_generation(
        name="query",
        input="What is the capital of France?",
        output="Paris",
        model="gemini-2.5-flash-lite",
    )

Environment Variables:
    LANGFUSE_PUBLIC_KEY: Langfuse public key
    LANGFUSE_SECRET_KEY: Langfuse secret key
    LANGFUSE_HOST: Langfuse host URL (optional, defaults to cloud)
    EXO_ENABLE_TRACING: Set to "false" to disable tracing (default: true)
"""

from __future__ import annotations

import functools
import os
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar, ParamSpec

# Try to import Langfuse
try:
    from langfuse import Langfuse
    from langfuse.decorators import observe as langfuse_observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None  # type: ignore
    langfuse_observe = None  # type: ignore


P = ParamSpec("P")
R = TypeVar("R")


def _is_tracing_enabled() -> bool:
    """Check if tracing is enabled via environment variable."""
    env_value = os.environ.get("EXO_ENABLE_TRACING", "true").lower()
    return env_value in ("true", "1", "yes", "on")


def _has_langfuse_credentials() -> bool:
    """Check if Langfuse credentials are configured."""
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    return bool(public_key and secret_key)


_langfuse_client: Langfuse | None = None


def get_langfuse_client() -> Langfuse | None:
    """
    Get the Langfuse client singleton.
    
    Returns None if Langfuse is not available or not configured.
    
    Returns:
        Langfuse client or None
    """
    global _langfuse_client
    
    if not LANGFUSE_AVAILABLE:
        return None
    
    if not _is_tracing_enabled():
        return None
    
    if not _has_langfuse_credentials():
        return None
    
    if _langfuse_client is None:
        _langfuse_client = Langfuse()
    
    return _langfuse_client


def observe(func: Callable[P, R] | None = None, *, name: str | None = None) -> Callable[P, R]:
    """
    Decorator to observe/trace a function using Langfuse.
    
    Gracefully degrades to no-op when:
    - Langfuse is not installed
    - LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not set
    - EXO_ENABLE_TRACING is set to "false"
    
    Args:
        func: The function to decorate
        name: Optional name for the trace (defaults to function name)
    
    Returns:
        Decorated function
    
    Example:
        @observe
        def my_function():
            ...
        
        @observe(name="custom_name")
        def another_function():
            ...
    """
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        # If Langfuse is not available or tracing is disabled, return no-op
        if not LANGFUSE_AVAILABLE or not _is_tracing_enabled() or not _has_langfuse_credentials():
            @functools.wraps(fn)
            def noop_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                return fn(*args, **kwargs)
            return noop_wrapper
        
        # Use Langfuse's observe decorator
        trace_name = name or fn.__name__
        return langfuse_observe(name=trace_name)(fn)  # type: ignore
    
    # Handle being called with or without arguments
    if func is None:
        return decorator  # type: ignore
    return decorator(func)


def trace_generation(
    name: str,
    input: str,  # noqa: A002
    output: str,
    model: str,
    metadata: dict[str, Any] | None = None,
    usage: dict[str, int] | None = None,
) -> None:
    """
    Trace a single LLM generation to Langfuse.
    
    Gracefully skips if Langfuse is not available or configured.
    
    Args:
        name: Name of the generation
        input: Input prompt/query
        output: Generated output
        model: Model name used
        metadata: Additional metadata
        usage: Token usage dict with keys like 'input_tokens', 'output_tokens'
    
    Example:
        trace_generation(
            name="summarize",
            input="Summarize this text...",
            output="The text discusses...",
            model="gemini-2.5-flash-lite",
            usage={"input_tokens": 100, "output_tokens": 50},
        )
    """
    client = get_langfuse_client()
    if client is None:
        return
    
    try:
        trace = client.trace(
            name=name,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
        )
        trace.generation(
            name=name,
            input=input,
            output=output,
            model=model,
            usage=usage,
        )
        client.flush()
    except Exception:
        # Silently ignore tracing errors to not affect main application
        pass


def trace_span(
    name: str,
    input: dict[str, Any] | None = None,  # noqa: A002
    output: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Trace a span (non-LLM operation) to Langfuse.
    
    Useful for tracing embeddings, database queries, or other operations.
    
    Args:
        name: Name of the span
        input: Input data
        output: Output data
        metadata: Additional metadata
    """
    client = get_langfuse_client()
    if client is None:
        return
    
    try:
        trace = client.trace(
            name=name,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
        )
        trace.span(
            name=name,
            input=input,
            output=output,
        )
        client.flush()
    except Exception:
        # Silently ignore tracing errors
        pass

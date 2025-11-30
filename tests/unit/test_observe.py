"""
Unit tests for the observe module.
"""

import os
from unittest.mock import patch

import pytest

from exo.llmops.observe import (
    observe,
    trace_generation,
    get_langfuse_client,
    _is_tracing_enabled,
    _has_langfuse_credentials,
    LANGFUSE_AVAILABLE,
)


class TestTracingEnabled:
    """Tests for _is_tracing_enabled function."""

    def test_enabled_by_default(self) -> None:
        """Tracing is enabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove any existing EXO_ENABLE_TRACING
            os.environ.pop("EXO_ENABLE_TRACING", None)
            assert _is_tracing_enabled() is True

    def test_enabled_explicitly(self) -> None:
        """Tracing can be explicitly enabled."""
        with patch.dict(os.environ, {"EXO_ENABLE_TRACING": "true"}):
            assert _is_tracing_enabled() is True

    def test_disabled_explicitly(self) -> None:
        """Tracing can be disabled via env var."""
        with patch.dict(os.environ, {"EXO_ENABLE_TRACING": "false"}):
            assert _is_tracing_enabled() is False

    def test_disabled_with_zero(self) -> None:
        """Tracing disabled with '0'."""
        with patch.dict(os.environ, {"EXO_ENABLE_TRACING": "0"}):
            assert _is_tracing_enabled() is False


class TestHasLangfuseCredentials:
    """Tests for _has_langfuse_credentials function."""

    def test_no_credentials(self) -> None:
        """Returns False when no credentials set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
            os.environ.pop("LANGFUSE_SECRET_KEY", None)
            assert _has_langfuse_credentials() is False

    def test_partial_credentials(self) -> None:
        """Returns False when only public key set."""
        with patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "pk-test"}, clear=True):
            os.environ.pop("LANGFUSE_SECRET_KEY", None)
            assert _has_langfuse_credentials() is False

    def test_full_credentials(self) -> None:
        """Returns True when both keys set."""
        with patch.dict(os.environ, {
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
        }):
            assert _has_langfuse_credentials() is True


class TestObserveDecorator:
    """Tests for the observe decorator."""

    def test_decorator_noop_without_langfuse(self) -> None:
        """Decorator is no-op when Langfuse not available."""
        # Even if Langfuse is installed, without credentials it should be no-op
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
            os.environ.pop("LANGFUSE_SECRET_KEY", None)
            
            @observe
            def my_function(x: int) -> int:
                return x * 2
            
            result = my_function(5)
            assert result == 10

    def test_decorator_noop_when_disabled(self) -> None:
        """Decorator is no-op when tracing disabled."""
        with patch.dict(os.environ, {"EXO_ENABLE_TRACING": "false"}):
            @observe
            def my_function(x: int) -> int:
                return x * 2
            
            result = my_function(5)
            assert result == 10

    def test_decorator_with_name(self) -> None:
        """Decorator accepts custom name."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
            
            @observe(name="custom_trace")
            def my_function(x: int) -> int:
                return x * 2
            
            result = my_function(5)
            assert result == 10

    def test_decorator_preserves_function_metadata(self) -> None:
        """Decorator preserves function name and docstring."""
        @observe
        def my_documented_function(x: int) -> int:
            """This is a docstring."""
            return x * 2
        
        assert my_documented_function.__name__ == "my_documented_function"
        assert "docstring" in (my_documented_function.__doc__ or "")


class TestTraceGeneration:
    """Tests for trace_generation function."""

    def test_trace_generation_noop_without_client(self) -> None:
        """trace_generation is no-op without Langfuse client."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
            
            # Should not raise
            trace_generation(
                name="test",
                input="Hello",
                output="World",
                model="test-model",
            )

    def test_trace_generation_noop_when_disabled(self) -> None:
        """trace_generation is no-op when tracing disabled."""
        with patch.dict(os.environ, {"EXO_ENABLE_TRACING": "false"}):
            # Should not raise
            trace_generation(
                name="test",
                input="Hello",
                output="World",
                model="test-model",
                metadata={"key": "value"},
                usage={"input_tokens": 10, "output_tokens": 5},
            )


class TestGetLangfuseClient:
    """Tests for get_langfuse_client function."""

    def test_returns_none_when_disabled(self) -> None:
        """Returns None when tracing is disabled."""
        with patch.dict(os.environ, {"EXO_ENABLE_TRACING": "false"}):
            client = get_langfuse_client()
            assert client is None

    def test_returns_none_without_credentials(self) -> None:
        """Returns None without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
            os.environ.pop("LANGFUSE_SECRET_KEY", None)
            client = get_langfuse_client()
            assert client is None

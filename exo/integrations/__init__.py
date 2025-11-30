"""
Integrations module for Exo.

Provides integrations with external tools:
- LangChain: ExoRetriever for RAG pipelines
- n8n: Webhook helpers for automation workflows
"""

# Lazy imports to avoid requiring optional dependencies
__all__ = ["ExoRetriever", "format_n8n_response", "validate_n8n_webhook"]


def __getattr__(name: str):
    """Lazy import integrations to avoid requiring optional dependencies."""
    if name == "ExoRetriever":
        from exo.integrations.langchain import ExoRetriever
        return ExoRetriever
    elif name in ("format_n8n_response", "validate_n8n_webhook"):
        from exo.integrations import n8n
        return getattr(n8n, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

"""
n8n integration helpers for Exo.

Provides utilities for formatting responses and validating webhook payloads
for n8n automation workflows.

Usage:
    from exo.integrations.n8n import format_n8n_response, validate_n8n_webhook

    # Format a response for n8n
    response = format_n8n_response(data, success=True)

    # Validate incoming webhook payload
    is_valid, error = validate_n8n_webhook(payload, required_fields=["text"])
"""

from datetime import datetime, timezone
from typing import Any


def format_n8n_response(
    data: dict[str, Any] | list[dict[str, Any]],
    success: bool = True,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Format a response in n8n-compatible format.

    n8n expects responses in a specific format for proper node chaining.
    This function ensures consistent response structure.

    Args:
        data: The main response data (dict or list of dicts)
        success: Whether the operation succeeded
        error: Error message if success is False
        metadata: Additional metadata to include

    Returns:
        n8n-compatible response dict

    Example:
        >>> format_n8n_response({"answer": "Hello"}, success=True)
        {
            "success": True,
            "data": {"answer": "Hello"},
            "timestamp": "2025-11-30T12:00:00Z",
            "metadata": {}
        }
    """
    response: dict[str, Any] = {
        "success": success,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "metadata": metadata or {},
    }

    if error:
        response["error"] = error

    # For list data, also include count
    if isinstance(data, list):
        response["count"] = len(data)

    return response


def validate_n8n_webhook(
    payload: dict[str, Any],
    required_fields: list[str] | None = None,
    optional_fields: list[str] | None = None,
) -> tuple[bool, str | None]:
    """
    Validate an incoming n8n webhook payload.

    Checks that required fields are present and have non-empty values.

    Args:
        payload: The incoming webhook payload
        required_fields: List of field names that must be present
        optional_fields: List of optional field names (for documentation)

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, "error message") if invalid

    Example:
        >>> validate_n8n_webhook({"text": "hello"}, required_fields=["text"])
        (True, None)

        >>> validate_n8n_webhook({}, required_fields=["text"])
        (False, "Missing required field: text")
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object"

    required = required_fields or []

    for field in required:
        if field not in payload:
            return False, f"Missing required field: {field}"

        value = payload[field]
        if value is None:
            return False, f"Field '{field}' cannot be null"

        if isinstance(value, str) and not value.strip():
            return False, f"Field '{field}' cannot be empty"

    return True, None


def format_ingest_response(
    memory_id: str | None,
    summary: str,
    commitment_count: int = 0,
    entity_count: int = 0,
) -> dict[str, Any]:
    """
    Format an ingest response for n8n.

    Provides a simplified response format suitable for n8n workflows.

    Args:
        memory_id: ID of the created memory
        summary: Summary of ingested content
        commitment_count: Number of commitments extracted
        entity_count: Number of entities extracted

    Returns:
        n8n-compatible ingest response
    """
    return format_n8n_response(
        {
            "id": memory_id,
            "summary": summary,
            "commitment_count": commitment_count,
            "entity_count": entity_count,
        },
        success=True,
        metadata={"operation": "ingest"},
    )


def format_query_response(
    answer: str,
    source_count: int = 0,
    confidence: float = 0.0,
    commitments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Format a query response for n8n.

    Provides a simplified response format suitable for n8n workflows.

    Args:
        answer: The generated answer
        source_count: Number of sources used
        confidence: Confidence score
        commitments: Related commitments found

    Returns:
        n8n-compatible query response
    """
    return format_n8n_response(
        {
            "answer": answer,
            "source_count": source_count,
            "confidence": confidence,
            "commitments": commitments or [],
        },
        success=True,
        metadata={"operation": "query"},
    )


def format_error_response(
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Format an error response for n8n.

    Args:
        error_code: Error code string
        message: Human-readable error message
        details: Additional error details

    Returns:
        n8n-compatible error response
    """
    return format_n8n_response(
        {
            "code": error_code,
            "message": message,
            "details": details or {},
        },
        success=False,
        error=message,
    )

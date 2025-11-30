"""
API key authentication middleware.

Validates X-API-Key header against EXO_API_KEY environment variable.
"""

import os
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse


# Paths that don't require authentication
PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}


async def api_key_middleware(request: Request, call_next: Callable) -> Response:
    """
    Validate API key for protected endpoints.

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response from next handler or 401 error
    """
    # Skip auth for public paths
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    # Get expected API key from environment
    expected_key = os.environ.get("EXO_API_KEY")

    # If no key is configured, allow all requests (dev mode)
    if not expected_key:
        return await call_next(request)

    # Check for API key in header
    provided_key = request.headers.get("X-API-Key")

    if not provided_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing X-API-Key header"},
        )

    if provided_key != expected_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid API key"},
        )

    return await call_next(request)

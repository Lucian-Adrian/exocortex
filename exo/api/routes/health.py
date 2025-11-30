"""
Health check endpoint.

Provides basic health and version information.
"""

from fastapi import APIRouter

from exo import __version__

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        Status and version information
    """
    return {
        "status": "ok",
        "version": __version__,
        "service": "exo",
    }


@router.get("/")
async def root() -> dict:
    """
    Root endpoint.

    Returns:
        Welcome message and API info
    """
    return {
        "message": "Welcome to Exo API",
        "version": __version__,
        "docs": "/docs",
    }

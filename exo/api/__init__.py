"""
REST API module for Exo.

Provides HTTP endpoints for ingest, query, and search operations.
"""

from exo.api.app import create_app, app

__all__ = ["create_app", "app"]

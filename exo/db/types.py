"""
Database type definitions.

Helper types for database results and query parameters.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class DBResult(BaseModel, Generic[T]):
    """Generic wrapper for database operation results."""

    data: list[T] | None = None
    count: int | None = None
    error: Any | None = None

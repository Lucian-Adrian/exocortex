"""
Executive OS (Exo) - Personal Knowledge Memory System

A pipeline-first architecture for capturing, enriching, and querying personal knowledge.
"""

__version__ = "0.1.0"
__author__ = "Exo Team"

from exo import schemas, db, ai, pipeline, parsers

__all__ = [
    "__version__",
    "schemas",
    "db",
    "ai",
    "pipeline",
    "parsers",
]

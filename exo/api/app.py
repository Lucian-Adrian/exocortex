"""
FastAPI application factory.

Creates the FastAPI app with lifespan management and routers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from exo import __version__
from exo.api.routes import health, ingest, query, search, commitments
from exo.api.middleware import api_key_middleware
from exo.api.webhooks import router as webhooks_router
from exo.pipeline import PipelineOrchestrator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan.

    Creates shared orchestrator instance on startup.
    """
    # Startup: create orchestrator
    app.state.orchestrator = PipelineOrchestrator()
    yield
    # Shutdown: cleanup if needed
    pass


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Exo API",
        description="Executive OS - Personal Knowledge Memory System API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add middleware
    app.middleware("http")(api_key_middleware)

    # Include routers
    app.include_router(health.router)
    app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
    app.include_router(query.router, prefix="/api/v1", tags=["query"])
    app.include_router(search.router, prefix="/api/v1", tags=["search"])
    app.include_router(commitments.router, prefix="/api/v1", tags=["commitments"])
    app.include_router(webhooks_router, prefix="/webhook", tags=["webhooks"])

    return app


# Create default app instance
app = create_app()

"""FastAPI application factory for Tensor Studio marketplace."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine, init_db
from app.api import plugins as plugins_router
from app.services.seed import seed_marketplace

log = logging.getLogger("tensor_studio")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Initialises the database schema and seeds default marketplace data
    on first run.  All routers are mounted here so the entry-point
    stays a single, discoverable location.
    """
    init_db()
    seed_marketplace()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(plugins_router.router, prefix="/api/v1")

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        """Liveness probe for container orchestrators."""
        return {"status": "ok"}

    log.info("Tensor Studio marketplace started v=%s", settings.app_version)
    return app


# Module-level app instance for uvicorn and ASGI hosts.
app = create_app()
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.scheduler.scheduler import shutdown_scheduler, start_scheduler

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    log.info("app_startup", app_name=settings.app_name, environment=settings.environment.value)
    start_scheduler()
    yield
    shutdown_scheduler()
    log.info("app_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    app.include_router(health_router)

    return app


app = create_app()

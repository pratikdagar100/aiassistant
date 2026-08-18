"""FastAPI application factory for PratikAI's backend."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    audit,
    avatar,
    chat,
    computer,
    entities,
    health,
    knowledge,
    learning,
    memory,
    models,
    permissions,
    settings as settings_routes,
    speech,
    tasks,
    training,
    vision,
)
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.seed import seed_default_entity

logger = get_logger("api")

_start_time = time.monotonic()


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("PratikAI backend starting up (phase=%s)", settings.phase)
    seed_default_entity()
    yield
    logger.info("PratikAI backend shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Local personal AI platform — backend API.",
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://{settings.frontend.host}:{settings.frontend.port}",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.start_time = _start_time

    app.include_router(health.router, prefix="/api/health", tags=["health"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(models.router, prefix="/api/models", tags=["models"])
    app.include_router(entities.router, prefix="/api/entities", tags=["entities"])
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
    app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
    app.include_router(speech.router, prefix="/api/speech", tags=["speech"])
    app.include_router(computer.router, prefix="/api/computer", tags=["computer"])
    app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
    app.include_router(permissions.router, prefix="/api/permissions", tags=["permissions"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(vision.router, prefix="/api/vision", tags=["vision"])
    app.include_router(avatar.router, prefix="/api/avatar", tags=["avatar"])
    app.include_router(learning.router, prefix="/api/learning", tags=["learning"])
    app.include_router(training.router, prefix="/api/training", tags=["training"])
    app.include_router(settings_routes.router, prefix="/api/settings", tags=["settings"])

    return app


app = create_app()

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.projects import router as projects_router
from app.api.v1.workspaces import router as workspaces_router
from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.migrations import ensure_project_billing_columns
from app.models import Project, Task, User, Workspace  # noqa: F401
from app.models.base import Base
from app.services.bootstrap_service import BootstrapService

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "Starting %s in %s environment.",
        settings.app_name,
        settings.environment,
    )
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    if settings.run_startup_migrations and settings.database_url.startswith("sqlite"):
        ensure_project_billing_columns(engine)
    db = SessionLocal()
    try:
        BootstrapService(db).ensure_admin_user()
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def healthcheck() -> JSONResponse:
        return JSONResponse({"status": "ok", "environment": settings.environment})

    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(workspaces_router, prefix=settings.api_v1_prefix)
    app.include_router(projects_router, prefix=settings.api_v1_prefix)
    app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
    app.include_router(admin_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()

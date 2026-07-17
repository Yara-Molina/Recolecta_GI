from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.core.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION
from api.db.session import Base, engine
from api.models import clasificacion as clasificacion_model  # noqa: F401
from api.routers.clasificacion import router as clasificacion_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


@app.get("/health", summary="Health check", tags=["Salud"])
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(clasificacion_router)

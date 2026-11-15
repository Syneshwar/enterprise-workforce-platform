
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

from app.models import RefreshToken, User


settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Temporary local-development setup.
    # Replace with Alembic migrations for deployment.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.service_name,
    description="Authentication Service for Enterprise Workforce Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth-service",
    }

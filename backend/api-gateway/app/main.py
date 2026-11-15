
import logging

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging


settings = get_settings()

configure_logging(settings.log_level)

logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.app_name,
    description="API Gateway for Enterprise Workforce Management Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.include_router(health_router)


@app.get("/")
async def root():
    logger.info("API Gateway root endpoint accessed")

    return {
        "message": "Enterprise Workforce API Gateway is running",
        "environment": settings.environment,
        "service": "api-gateway",
    }

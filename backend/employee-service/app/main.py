
from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text

from app.api.routes.employees import router as employee_router
from app.core.config import get_settings
from app.db.session import engine


settings = get_settings()

app = FastAPI(
    title=settings.service_name,
    description="Employee management microservice for WorkforceHub.",
    version="1.0.0",
)

# Register Employee API routes
app.include_router(employee_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Enterprise Workforce Employee Service is running",
        "service": "employee-service",
        "environment": settings.environment,
    }


@app.get("/health/live", tags=["Health"])
def health_live():
    return {
        "status": "alive",
        "service": "employee-service",
    }


@app.get("/health/ready", tags=["Health"])
def health_ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Employee Service database is unavailable.",
        ) from exc

    return {
        "status": "ready",
        "database": "connected",
    }


from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "Enterprise Workforce Employee Service"
    environment: str = "development"

    database_url: str = "sqlite:///./employee_service.db"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    auth_service_base_url: str = "http://127.0.0.1:8001"
    auth_service_api_key: str

    model_config = SettingsConfigDict(
        env_prefix="EMPLOYEE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

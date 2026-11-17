
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "Enterprise Workforce Authentication Service"
    environment: str = "development"

    database_url: str = "sqlite:///./auth_service.db"

    jwt_secret_key: str = "development-only-change-this-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_prefix="AUTH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    internal_service_api_key: str

    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: str = "lax"

    csrf_secret_key: str = "development-only-change-this-csrf-secret-key"

    allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

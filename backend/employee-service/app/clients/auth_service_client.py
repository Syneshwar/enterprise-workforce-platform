
import httpx

from app.core.config import get_settings


class AuthServiceError(Exception):
    """Base exception for Auth Service communication errors."""


class AuthServiceUserNotFound(AuthServiceError):
    """Raised when the requested account does not exist or is inactive."""


class AuthServiceClient:
    """HTTP client for trusted communication with Auth Service."""

    def __init__(self):
        self.settings = get_settings()

    def get_active_user(self, user_id: int) -> dict:
        url = (
            f"{self.settings.auth_service_base_url.rstrip('/')}"
            f"/auth/internal/users/{user_id}"
        )

        headers = {
            "X-Internal-Service-Key": self.settings.auth_service_api_key
        }

        try:
            response = httpx.get(
                url,
                headers=headers,
                timeout=5.0,
            )

            if response.status_code == 404:
                raise AuthServiceUserNotFound(
                    "The Auth Service account does not exist or is inactive."
                )

            if response.status_code != 200:
                raise AuthServiceError(
                    "Auth Service could not verify the user account."
                )

            user = response.json()

            if not user.get("is_active"):
                raise AuthServiceUserNotFound(
                    "The Auth Service account is inactive."
                )

            return user

        except httpx.RequestError as exc:
            raise AuthServiceError(
                "Unable to communicate with Auth Service."
            ) from exc

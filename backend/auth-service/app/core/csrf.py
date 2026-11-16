import hashlib
import hmac
import secrets

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


settings = get_settings()


def create_csrf_token() -> str:
    """
    Generate a signed CSRF token.

    Format:
        random_value.signature
    """
    random_value = secrets.token_urlsafe(32)

    signature = hmac.new(
        settings.csrf_secret_key.encode("utf-8"),
        random_value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{random_value}.{signature}"


def is_valid_csrf_token(token: str) -> bool:
    """Validate the signature of a CSRF token."""
    try:
        random_value, supplied_signature = token.rsplit(".", 1)
    except ValueError:
        return False

    expected_signature = hmac.new(
        settings.csrf_secret_key.encode("utf-8"),
        random_value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        supplied_signature,
        expected_signature,
    )


def validate_csrf_request(request: Request) -> None:
    """
    Validate Origin and signed double-submit CSRF token.

    Required:
    - Trusted Origin
    - CSRF cookie
    - Matching X-CSRF-Token header
    - Valid HMAC signature
    """
    origin = request.headers.get("origin")

    if not origin or origin not in settings.allowed_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing request origin.",
        )

    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")

    if not csrf_cookie or not csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token is missing.",
        )

    if not hmac.compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token mismatch.",
        )

    if not is_valid_csrf_token(csrf_cookie):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token.",
        )

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings


settings = get_settings()

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """Authenticated user information extracted from JWT."""

    user_id: int
    role: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> CurrentUser:

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    if credentials.scheme.lower() != "bearer":
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "iat", "type", "role"]},
        )

        if payload.get("type") != "access":
            raise unauthorized

        user_id = int(payload["sub"])
        role = payload["role"]

        if user_id <= 0 or not isinstance(role, str) or not role.strip():
            raise unauthorized

        return CurrentUser(
            user_id=user_id,
            role=role.lower(),
        )

    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise unauthorized


def require_hr_or_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Restrict employee management to HR and Admin roles."""

    if current_user.role not in {"hr", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )

    return current_user

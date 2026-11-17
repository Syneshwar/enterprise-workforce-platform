
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import UserRegisterRequest


settings = get_settings()


def register_user(
    db: Session,
    user_data: UserRegisterRequest,
) -> User:
    normalized_email = str(user_data.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if existing_user:
        raise ValueError("Email address is already registered.")

    user = User(
        email=normalized_email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role="employee",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    normalized_email = email.strip().lower()

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    if not user.is_active:
        return None

    return user


def generate_user_access_token(user: User) -> str:
    """
    Generate an access token containing the user's identity and role.
    """
    return create_access_token(
        subject=str(user.id),
        role=user.role,
    )


def get_access_token_expiry_seconds() -> int:
    return settings.access_token_expire_minutes * 60

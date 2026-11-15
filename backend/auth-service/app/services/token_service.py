
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import generate_refresh_token, hash_refresh_token
from app.models.refresh_token import RefreshToken
from app.models.user import User

settings = get_settings()


def get_refresh_token_expiry_seconds() -> int:
    """Return the configured refresh-token lifetime in seconds."""
    return settings.refresh_token_expire_days * 24 * 60 * 60


def create_refresh_token(db: Session, user: User) -> str:
    """Generate and persist a refresh-token hash."""
    raw_token = generate_refresh_token()

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=expires_at,
    )

    db.add(token_record)
    db.commit()
    db.refresh(token_record)

    return raw_token


def rotate_refresh_token(
    db: Session,
    raw_token: str,
) -> tuple[str, User] | None:
    """
    Validate a refresh token and atomically replace it.

    Returns:
        (new_raw_token, user) when successful.
        None when the token is invalid, expired, revoked,
        or belongs to an inactive/nonexistent user.
    """
    token_hash = hash_refresh_token(raw_token)

    token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
    )

    if token_record is None or token_record.revoked_at is not None:
        return None

    now = datetime.now(timezone.utc)

    # SQLite may return timezone-naive datetimes.
    token_expiry = token_record.expires_at
    if token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=timezone.utc)

    if token_expiry <= now:
        return None

    user = db.get(User, token_record.user_id)

    if user is None or not user.is_active:
        return None

    new_raw_token = generate_refresh_token()

    new_token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_raw_token),
        expires_at=now + timedelta(
            days=settings.refresh_token_expire_days
        ),
    )

    try:
        # Conditional update ensures only one concurrent request
        # can successfully consume the old refresh token.
        result = db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.id == token_record.id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now.replace(tzinfo=None),
            )
            .values(revoked_at=now)
        )

        if result.rowcount != 1:
            db.rollback()
            return None

        db.add(new_token_record)
        db.flush()

        token_record.replaced_by_id = new_token_record.id

        db.commit()

        return new_raw_token, user

    except Exception:
        db.rollback()
        raise


def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    """Revoke an active refresh token.

    Returns True when an active token is revoked.
    Returns False when the token is invalid or already revoked.
    """
    token_hash = hash_refresh_token(raw_token)

    token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
    )

    if token_record is None or token_record.revoked_at is not None:
        return False

    token_record.revoked_at = datetime.now(timezone.utc)

    db.commit()

    return True

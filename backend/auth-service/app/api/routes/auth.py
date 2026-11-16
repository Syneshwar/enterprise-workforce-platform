from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.csrf import create_csrf_token, validate_csrf_request
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    generate_user_access_token,
    get_access_token_expiry_seconds,
    register_user,
)
from app.services.token_service import (
    create_refresh_token,
    get_refresh_token_expiry_seconds,
    revoke_refresh_token,
    rotate_refresh_token,
)

from app.core.csrf import (
    create_csrf_token,
    validate_csrf_request,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

settings = get_settings()


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Store the refresh token in a secure, HttpOnly cookie."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        max_age=get_refresh_token_expiry_seconds(),
        path="/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    """Remove the refresh-token cookie from the browser."""
    response.delete_cookie(
        key="refresh_token",
        path="/auth",
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )

def set_csrf_cookie(response: Response) -> None:
    csrf_token = create_csrf_token()

    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        max_age=get_refresh_token_expiry_seconds(),
        path="/",
    )


def clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie(
        key="csrf_token",
        path="/",
        httponly=False,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        return register_user(db, user_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        credentials.email,
        credentials.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    refresh_token = create_refresh_token(db, user)
    set_refresh_cookie(response, refresh_token)
    set_csrf_cookie(response)

    return TokenResponse(
        access_token=generate_user_access_token(user),
        token_type="bearer",
        expires_in=get_access_token_expiry_seconds(),
        user=user,
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[Depends(validate_csrf_request)],
)
def refresh_access_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing.",
        )

    rotated = rotate_refresh_token(db, refresh_token)

    if rotated is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid, expired, or revoked.",
        )

    new_refresh_token, user = rotated

    set_refresh_cookie(response, new_refresh_token)
    set_csrf_cookie(response)

    return TokenResponse(
        access_token=generate_user_access_token(user),
        token_type="bearer",
        expires_in=get_access_token_expiry_seconds(),
        user=user,
    )


@router.post(
    "/logout",
    dependencies=[Depends(validate_csrf_request)],
)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token:
        revoke_refresh_token(db, refresh_token)

    clear_refresh_cookie(response)
    clear_csrf_cookie(response)

    return {"message": "Successfully logged out."}
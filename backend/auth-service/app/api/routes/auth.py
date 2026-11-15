
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.models.user import User

from app.db.session import get_db
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
)

from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    RefreshTokenRequest,
)

from app.services.token_service import (
    create_refresh_token,
    get_refresh_token_expiry_seconds,
    rotate_refresh_token,
    revoke_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


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

    access_token = generate_user_access_token(user)
    refresh_token = create_refresh_token(db, user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=get_access_token_expiry_seconds(),
        refresh_expires_in=get_refresh_token_expiry_seconds(),
        user=user,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    result = rotate_refresh_token(db, request.refresh_token)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_refresh_token, user = result

    new_access_token = generate_user_access_token(user)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=get_access_token_expiry_seconds(),
        refresh_expires_in=get_refresh_token_expiry_seconds(),
        user=user,
    )


@router.post("/logout")
def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    revoked = revoke_refresh_token(db, request.refresh_token)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or already revoked refresh token.",
        )

    return {
        "message": "Successfully logged out."
    }



@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user

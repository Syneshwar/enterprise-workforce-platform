
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.csrf import create_csrf_token
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.refresh_token import RefreshToken


# ---------------------------------------------------------
# Test configuration
# ---------------------------------------------------------

TRUSTED_ORIGIN = "http://localhost:5173"


@pytest.fixture
def client(monkeypatch):
    # Create an isolated in-memory SQLite database for each test.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr("app.main.engine", test_engine)
    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@contextmanager
def db_session_context():
    """Access the isolated database used by the current test."""
    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        yield db
    finally:
        db_generator.close()


# ---------------------------------------------------------
# Test helper functions
# ---------------------------------------------------------

def register_test_user(client):
    return client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test Employee",
            "password": "SecurePass@123",
        },
    )


def login_test_user(client):
    return client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass@123",
        },
    )


def set_refresh_cookie(client, raw_token):
    """Explicitly set a refresh token for cookie-based API tests."""
    client.cookies.set(
        "refresh_token",
        raw_token,
        path="/auth",
    )


def set_csrf_cookie(client, token=None):
    """Set a valid CSRF cookie for protected requests."""
    token = token or create_csrf_token()

    client.cookies.set(
        "csrf_token",
        token,
        path="/",
    )

    return token


def csrf_headers(client):
    """Return the trusted Origin and matching CSRF header."""
    token = client.cookies.get("csrf_token")

    if not token:
        token = set_csrf_cookie(client)

    return {
        "Origin": TRUSTED_ORIGIN,
        "X-CSRF-Token": token,
    }


# ---------------------------------------------------------
# Registration tests
# ---------------------------------------------------------

def test_user_registration_success(client):
    response = register_test_user(client)

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert response.json()["role"] == "employee"
    assert "hashed_password" not in response.json()
    assert "password" not in response.json()


def test_duplicate_email_registration(client):
    first_response = register_test_user(client)
    second_response = register_test_user(client)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


# ---------------------------------------------------------
# Login tests
# ---------------------------------------------------------

def test_user_login_success(client):
    register_test_user(client)

    response = login_test_user(client)

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["token_type"] == "bearer"
    assert response_data["expires_in"] == 1800
    assert response_data["access_token"]
    assert response_data["user"]["email"] == "test@example.com"

    # Refresh token must not be exposed in JSON.
    assert "refresh_token" not in response_data
    assert "refresh_expires_in" not in response_data

    # Refresh token must be delivered as an HttpOnly cookie.
    refresh_cookie_header = [
        cookie
        for cookie in response.headers.get_list("set-cookie")
        if cookie.startswith("refresh_token=")
    ]

    assert refresh_cookie_header
    assert "httponly" in refresh_cookie_header[0].lower()
    assert client.cookies.get("refresh_token")

    # CSRF token must be available to frontend JavaScript.
    csrf_cookie_header = [
        cookie
        for cookie in response.headers.get_list("set-cookie")
        if cookie.startswith("csrf_token=")
    ]

    assert csrf_cookie_header
    assert "httponly" not in csrf_cookie_header[0].lower()
    assert client.cookies.get("csrf_token")


def test_login_with_wrong_password(client):
    register_test_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword@123",
        },
    )

    assert response.status_code == 401


# ---------------------------------------------------------
# Access-token tests
# ---------------------------------------------------------

def test_get_current_user_with_valid_token(client):
    register_test_user(client)

    login_response = login_test_user(client)

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["full_name"] == "Test Employee"


def test_get_current_user_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_get_current_user_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401


def test_get_current_user_with_expired_token(client):
    register_test_user(client)

    expired_token = create_access_token(
        subject="1",
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401


# ---------------------------------------------------------
# Refresh-token rotation tests
# ---------------------------------------------------------

def test_refresh_token_rotation_success(client):
    register_test_user(client)

    login_test_user(client)

    old_refresh_token = client.cookies.get("refresh_token")

    assert old_refresh_token

    response = client.post(
        "/auth/refresh",
        headers=csrf_headers(client),
    )

    assert response.status_code == 200

    response_data = response.json()

    new_refresh_token = client.cookies.get("refresh_token")

    assert response_data["access_token"]
    assert "refresh_token" not in response_data
    assert response_data["user"]["email"] == "test@example.com"

    assert new_refresh_token
    assert new_refresh_token != old_refresh_token

    # Verify that the original token cannot be reused.
    set_refresh_cookie(client, old_refresh_token)

    old_token_response = client.post(
        "/auth/refresh",
        headers=csrf_headers(client),
    )

    assert old_token_response.status_code == 401


def test_refresh_token_reuse_rejected(client):
    register_test_user(client)

    login_test_user(client)

    old_refresh_token = client.cookies.get("refresh_token")

    assert old_refresh_token

    first_refresh = client.post(
        "/auth/refresh",
        headers=csrf_headers(client),
    )

    assert first_refresh.status_code == 200

    # Attempt to reuse the original token.
    set_refresh_cookie(client, old_refresh_token)

    second_refresh = client.post(
        "/auth/refresh",
        headers=csrf_headers(client),
    )

    assert second_refresh.status_code == 401


def test_refresh_with_invalid_token(client):
    set_csrf_cookie(client)
    set_refresh_cookie(client, "invalid-refresh-token")

    response = client.post(
        "/auth/refresh",
        headers=csrf_headers(client),
    )

    assert response.status_code == 401


def test_refresh_with_expired_token(client):
    register_test_user(client)

    raw_token = generate_refresh_token()

    with db_session_context() as db:
        from app.models.user import User

        user = db.scalar(
            select(User).where(User.email == "test@example.com")
        )

        expired_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        db.add(expired_record)
        db.commit()

    set_refresh_cookie(client, raw_token)

    response = client.post(
        "/auth/refresh",
        headers=csrf_headers(client),
    )

    assert response.status_code == 401


def test_refresh_with_revoked_token(client):
    register_test_user(client)

    login_test_user(client)

    raw_token = client.cookies.get("refresh_token")

    assert raw_token

    with db_session_context() as db:
        token_record = db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(raw_token)
            )
        )

        assert token_record is not None

        token_record.revoked_at = datetime.now(timezone.utc)
        db.commit()

    set_refresh_cookie(client, raw_token)

    response = client.post(
        "/auth/refresh",
        headers=csrf_headers(client),
    )

    assert response.status_code == 401


# ---------------------------------------------------------
# Logout tests
# ---------------------------------------------------------

def test_logout_success(client):
    register_test_user(client)

    login_test_user(client)

    refresh_token = client.cookies.get("refresh_token")

    assert refresh_token

    response = client.post(
        "/auth/logout",
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out."

    # Verify refresh cookie is cleared.
    assert client.cookies.get("refresh_token") is None

    # Verify CSRF cookie is cleared.
    assert client.cookies.get("csrf_token") is None

    # Verify that the database token has been revoked.
    with db_session_context() as db:
        token_record = db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(refresh_token)
            )
        )

        assert token_record is not None
        assert token_record.revoked_at is not None


def test_logout_with_invalid_token(client):
    set_csrf_cookie(client)
    set_refresh_cookie(client, "invalid-refresh-token")

    response = client.post(
        "/auth/logout",
        headers=csrf_headers(client),
    )

    # Logout is intentionally idempotent.
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out."


def test_logout_with_already_revoked_token(client):
    register_test_user(client)

    login_test_user(client)

    refresh_token = client.cookies.get("refresh_token")

    assert refresh_token

    with db_session_context() as db:
        token_record = db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(refresh_token)
            )
        )

        assert token_record is not None

        token_record.revoked_at = datetime.now(timezone.utc)
        db.commit()

    response = client.post(
        "/auth/logout",
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    assert client.cookies.get("refresh_token") is None
    assert client.cookies.get("csrf_token") is None


def test_refresh_after_logout_is_rejected(client):
    register_test_user(client)

    login_test_user(client)

    logout_response = client.post(
        "/auth/logout",
        headers=csrf_headers(client),
    )

    assert logout_response.status_code == 200
    assert client.cookies.get("refresh_token") is None

    # Logout clears the CSRF cookie. Set a fresh valid CSRF cookie
    # so this test verifies the missing refresh token behavior.
    set_csrf_cookie(client)

    refresh_response = client.post(
        "/auth/refresh",
        headers=csrf_headers(client),
    )

    assert refresh_response.status_code == 401


# ---------------------------------------------------------
# CSRF protection tests
# ---------------------------------------------------------

def test_refresh_without_csrf_header_rejected(client):
    register_test_user(client)
    login_test_user(client)

    response = client.post(
        "/auth/refresh",
        headers={
            "Origin": TRUSTED_ORIGIN,
        },
    )

    assert response.status_code == 403


def test_refresh_with_invalid_origin_rejected(client):
    register_test_user(client)
    login_test_user(client)

    response = client.post(
        "/auth/refresh",
        headers={
            "Origin": "http://malicious.example",
            "X-CSRF-Token": client.cookies.get("csrf_token"),
        },
    )

    assert response.status_code == 403


def test_logout_without_csrf_header_rejected(client):
    register_test_user(client)
    login_test_user(client)

    response = client.post(
        "/auth/logout",
        headers={
            "Origin": TRUSTED_ORIGIN,
        },
    )

    assert response.status_code == 403

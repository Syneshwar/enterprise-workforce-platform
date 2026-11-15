from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app


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

    # The application lifespan creates tables using app.main.engine.
    # Redirect it to the isolated test database too.
    monkeypatch.setattr("app.main.engine", test_engine)
    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


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


def test_user_login_success(client):
    register_test_user(client)

    response = login_test_user(client)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["expires_in"] == 1800
    assert response.json()["access_token"]
    assert response.json()["user"]["email"] == "test@example.com"


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
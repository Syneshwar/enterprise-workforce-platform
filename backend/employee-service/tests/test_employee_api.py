
import pytest

from app.clients.auth_service_client import (
    AuthServiceClient,
    AuthServiceError,
    AuthServiceUserNotFound,
)


@pytest.fixture
def employee_payload():
    return {
        "first_name": "Eshwar",
        "last_name": "Kumar",
        "email": "eshwar.test@example.com",
        "phone": "9876543210",
        "department": "Engineering",
        "designation": "Python Backend Developer",
        "date_of_joining": "2022-09-01",
        "employment_type": "full_time",
    }


@pytest.fixture(autouse=True)
def mock_auth_service(monkeypatch):
    """
    Mock Auth Service communication for Employee Service API tests.
    """

    def mock_get_active_user(self, user_id):
        return {
            "id": user_id,
            "email": "eshwar.test@example.com",
            "full_name": "Eshwar Kumar",
            "role": "employee",
            "is_active": True,
        }

    monkeypatch.setattr(
        AuthServiceClient,
        "get_active_user",
        mock_get_active_user,
    )


def create_employee(client, make_token, payload, user_id=1001):
    """Create an employee using an HR token."""

    token = make_token(user_id=9001, role="hr")

    return client.post(
        f"/employees/{user_id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )


def test_create_employee(client, make_token, employee_payload):
    response = create_employee(
        client,
        make_token,
        employee_payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == 1001
    assert data["first_name"] == "Eshwar"
    assert data["email"] == "eshwar.test@example.com"
    assert data["employee_code"].startswith("EMP-")
    assert data["is_active"] is True


def test_list_employees(client, make_token, employee_payload):
    create_response = create_employee(
        client,
        make_token,
        employee_payload,
    )

    assert create_response.status_code == 201

    token = make_token(user_id=9001, role="admin")

    response = client.get(
        "/employees",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["email"] == employee_payload["email"]


def test_get_employee_by_id(client, make_token, employee_payload):
    create_response = create_employee(
        client,
        make_token,
        employee_payload,
    )

    employee_id = create_response.json()["id"]

    token = make_token(user_id=9001, role="hr")

    response = client.get(
        f"/employees/{employee_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == employee_id


def test_employee_can_view_own_profile(
    client,
    make_token,
    employee_payload,
):
    create_response = create_employee(
        client,
        make_token,
        employee_payload,
    )

    assert create_response.status_code == 201

    token = make_token(user_id=1001, role="employee")

    response = client.get(
        "/employees/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == 1001
    assert response.json()["email"] == employee_payload["email"]


def test_update_employee(client, make_token, employee_payload):
    create_response = create_employee(
        client,
        make_token,
        employee_payload,
    )

    employee_id = create_response.json()["id"]

    token = make_token(user_id=9001, role="hr")

    response = client.patch(
        f"/employees/{employee_id}",
        json={"designation": "Senior Python Developer"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["designation"] == "Senior Python Developer"


def test_deactivate_employee(client, make_token, employee_payload):
    create_response = create_employee(
        client,
        make_token,
        employee_payload,
    )

    employee_id = create_response.json()["id"]

    token = make_token(user_id=9001, role="admin")

    response = client.delete(
        f"/employees/{employee_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_employee_cannot_list_all_employees(
    client,
    make_token,
):
    token = make_token(user_id=1001, role="employee")

    response = client.get(
        "/employees",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_request_without_token_is_rejected(client):
    response = client.get("/employees")

    assert response.status_code == 401


# New service-to-service security tests


def test_create_employee_rejects_unverified_user(
    client,
    make_token,
    employee_payload,
    monkeypatch,
):
    def mock_user_not_found(self, user_id):
        raise AuthServiceUserNotFound("Active user account not found.")

    monkeypatch.setattr(
        AuthServiceClient,
        "get_active_user",
        mock_user_not_found,
    )

    response = create_employee(
        client,
        make_token,
        employee_payload,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Active user account not found."


def test_create_employee_handles_auth_service_failure(
    client,
    make_token,
    employee_payload,
    monkeypatch,
):
    def mock_auth_failure(self, user_id):
        raise AuthServiceError("Unable to communicate with Auth Service.")

    monkeypatch.setattr(
        AuthServiceClient,
        "get_active_user",
        mock_auth_failure,
    )

    response = create_employee(
        client,
        make_token,
        employee_payload,
    )

    assert response.status_code == 502


def test_create_employee_rejects_email_mismatch(
    client,
    make_token,
    employee_payload,
):
    employee_payload["email"] = "different@example.com"

    response = create_employee(
        client,
        make_token,
        employee_payload,
    )

    assert response.status_code == 409
    assert "email does not match" in response.json()["detail"].lower()


def test_employee_cannot_create_employee_profile(
    client,
    make_token,
    employee_payload,
):
    token = make_token(user_id=1001, role="employee")

    response = client.post(
        "/employees/1002",
        json=employee_payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

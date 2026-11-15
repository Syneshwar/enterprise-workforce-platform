
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "api-gateway"


def test_liveness_check():
    response = client.get("/health/live")

    assert response.status_code == 200

    assert response.json() == {
        "status": "alive",
        "service": "api-gateway",
    }


def test_readiness_check():
    response = client.get("/health/ready")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ready",
        "service": "api-gateway",
    }

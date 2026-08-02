from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy v5.0"
    assert "app_name" in data


def test_liveness_probe():
    response = client.get("/health/liveness")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@patch("app.main.check_db_connection", return_value=True)
def test_readiness_probe_success(mock_check):
    response = client.get("/health/readiness")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}


@patch("app.main.check_db_connection", return_value=False)
def test_readiness_probe_failure(mock_check):
    response = client.get("/health/readiness")
    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "database": "disconnected"}


def test_create_and_get_items():
    item_payload = {"id": 1, "name": "Widget A", "description": "DevOps test item"}
    post_response = client.post("/items", json=item_payload)
    assert post_response.status_code == 201
    assert post_response.json() == item_payload

    get_response = client.get("/items")
    assert get_response.status_code == 200
    items = get_response.json()
    assert len(items) >= 1
    assert items[0]["id"] == 1

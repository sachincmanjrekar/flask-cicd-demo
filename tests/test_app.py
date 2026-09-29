import pytest

from app import app as flask_app
from app import tasks


@pytest.fixture(autouse=True)
def clear_tasks():
    tasks.clear()
    yield
    tasks.clear()


@pytest.fixture
def client():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_list_tasks_empty(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_task(client):
    response = client.post("/tasks", json={"title": "Prep for Accenture interview"})
    assert response.status_code == 201
    body = response.get_json()
    assert body["title"] == "Prep for Accenture interview"
    assert body["done"] is False
    assert "id" in body


def test_create_task_without_title(client):
    response = client.post("/tasks", json={})
    assert response.status_code == 400


def test_get_task(client):
    created = client.post("/tasks", json={"title": "Learn CI/CD"}).get_json()
    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.get_json()["title"] == "Learn CI/CD"


def test_get_missing_task(client):
    response = client.get("/tasks/999")
    assert response.status_code == 404


def test_update_task(client):
    created = client.post("/tasks", json={"title": "Deploy app"}).get_json()
    response = client.patch(f"/tasks/{created['id']}", json={"done": True})
    assert response.status_code == 200
    assert response.get_json()["done"] is True


def test_delete_task(client):
    created = client.post("/tasks", json={"title": "Temp"}).get_json()
    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/tasks/{created['id']}").status_code == 404

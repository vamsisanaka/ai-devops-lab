import pytest
from app.main import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"

def test_create_task(client):
    res = client.post("/tasks", json={"title": "Learn AI DevOps"})
    assert res.status_code == 201
    assert res.get_json()["title"] == "Learn AI DevOps"

def test_get_tasks(client):
    res = client.get("/tasks")
    assert res.status_code == 200

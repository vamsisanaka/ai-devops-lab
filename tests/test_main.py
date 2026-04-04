import pytest
from app.main import app, tasks  # noqa: F401


@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Reset tasks before each test
    global tasks
    tasks.clear()
    with app.test_client() as client:
        yield client


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "version" in data


def test_get_tasks_empty(client):
    res = client.get("/tasks")
    assert res.status_code == 200
    data = res.get_json()
    assert data["tasks"] == []
    assert data["count"] == 0


def test_get_tasks_with_data(client):
    # First create a task
    client.post("/tasks", json={"title": "Test Task"})
    res = client.get("/tasks")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["tasks"]) == 1
    assert data["count"] == 1
    assert data["tasks"][0]["title"] == "Test Task"
    assert data["tasks"][0]["id"] == 1
    assert data["tasks"][0]["done"] is False
    assert data["tasks"][0]["priority"] == "medium"


def test_create_task_success(client):
    res = client.post("/tasks", json={"title": "Learn AI DevOps"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "Learn AI DevOps"
    assert data["id"] == 1
    assert data["done"] is False
    assert data["priority"] == "medium"  # default priority


def test_create_task_with_priority(client):
    res = client.post(
        "/tasks", json={"title": "High Priority Task", "priority": "high"}
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "High Priority Task"
    assert data["priority"] == "high"


def test_create_task_invalid_priority(client):
    res = client.post("/tasks", json={"title": "Task", "priority": "urgent"})
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data
    assert "priority must be one of" in data["error"]


def test_create_task_missing_title(client):
    res = client.post("/tasks", json={})
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data
    assert "title is required" in data["error"]


def test_create_task_no_json(client):
    res = client.post("/tasks")
    assert (
        res.status_code == 415
    )  # Flask returns 415 for unsupported media type when no JSON body


def test_update_task_success(client):
    # Create a task first
    client.post("/tasks", json={"title": "Test Task"})
    res = client.put("/tasks/1", json={"done": True})
    assert res.status_code == 200
    data = res.get_json()
    assert data["id"] == 1
    assert data["title"] == "Test Task"
    assert data["done"] is True


def test_update_task_not_found(client):
    res = client.put("/tasks/999", json={"done": True})
    assert res.status_code == 404
    data = res.get_json()
    assert "error" in data
    assert "task not found" in data["error"]


def test_update_task_no_json(client):
    # Create a task first
    client.post("/tasks", json={"title": "Test Task"})
    res = client.put("/tasks/1")  # No JSON body
    assert res.status_code == 415  # Flask returns 415 for no body


def test_delete_task_success(client):
    # Create a task first
    client.post("/tasks", json={"title": "Test Task"})
    res = client.delete("/tasks/1")
    assert res.status_code == 200
    data = res.get_json()
    assert "message" in data
    assert "task deleted" in data["message"]
    # Verify task is deleted
    res2 = client.get("/tasks")
    assert res2.get_json()["count"] == 0


def test_delete_task_not_found(client):
    res = client.delete("/tasks/999")
    assert res.status_code == 404
    data = res.get_json()
    assert "error" in data
    assert "task not found" in data["error"]


def test_delete_task_invalid_id(client):
    res = client.delete("/tasks/abc")
    assert res.status_code == 404  # Flask will return 404 for invalid int conversion

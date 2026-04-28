import pytest
from datetime import datetime, timedelta

def test_filter_by_status(client):
    # Create tasks with different statuses
    client.post("/api/v1/tasks", json={"title": "Task 1", "status": "Not Started"})
    client.post("/api/v1/tasks", json={"title": "Task 2", "status": "In Progress"})
    client.post("/api/v1/tasks", json={"title": "Task 3", "status": "Completed"})
    
    # Filter by "In Progress"
    response = client.get("/api/v1/tasks", params={"status": "In Progress"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task 2"

def test_filter_by_priority(client):
    # Create tasks with different priorities
    client.post("/api/v1/tasks", json={"title": "Task 1", "priority": "Low"})
    client.post("/api/v1/tasks", json={"title": "Task 2", "priority": "Medium"})
    client.post("/api/v1/tasks", json={"title": "Task 3", "priority": "High"})
    
    # Filter by "High"
    response = client.get("/api/v1/tasks", params={"priority": "High"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task 3"

def test_filter_by_is_blocked(client):
    # Create tasks
    res1 = client.post("/api/v1/tasks", json={"title": "Task 1", "status": "Not Started"})
    id1 = res1.json()["id"]
    # Task 2 is blocked by Task 1
    client.post("/api/v1/tasks", json={"title": "Task 2", "dependency_ids": [id1]})
    
    # Filter by is_blocked=True
    response = client.get("/api/v1/tasks", params={"is_blocked": True})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task 2"
    
    # Filter by is_blocked=False
    response = client.get("/api/v1/tasks", params={"is_blocked": False})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task 1"

def test_filter_by_due_date(client):
    now = datetime.utcnow()
    past = (now - timedelta(days=1)).isoformat()
    future = (now + timedelta(days=1)).isoformat()
    
    client.post("/api/v1/tasks", json={"title": "Past Task", "due_date": past})
    client.post("/api/v1/tasks", json={"title": "Future Task", "due_date": future})
    
    # Filter due_date_before=now
    response = client.get("/api/v1/tasks", params={"due_date_before": now.isoformat()})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Past Task"
    
    # Filter due_date_after=now
    response = client.get("/api/v1/tasks", params={"due_date_after": now.isoformat()})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Future Task"

def test_mandatory_filter_archived(client):
    client.post("/api/v1/tasks", json={"title": "Active Task", "status": "Not Started"})
    client.post("/api/v1/tasks", json={"title": "Archived Task", "status": "Archived"})
    
    # Default list should NOT include Archived
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Active Task"
    
    # Requesting Archived should include it
    response = client.get("/api/v1/tasks", params={"status": "Archived"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Archived Task"

def test_sorting(client):
    client.post("/api/v1/tasks", json={"title": "B Task", "priority": "Medium"})
    client.post("/api/v1/tasks", json={"title": "A Task", "priority": "High"})
    client.post("/api/v1/tasks", json={"title": "C Task", "priority": "Low"})
    
    # Sort by name (title) asc
    response = client.get("/api/v1/tasks", params={"sort_by": "name", "order": "asc"})
    data = response.json()
    assert data[0]["title"] == "A Task"
    assert data[1]["title"] == "B Task"
    assert data[2]["title"] == "C Task"
    
    # Sort by name (title) desc
    response = client.get("/api/v1/tasks", params={"sort_by": "name", "order": "desc"})
    data = response.json()
    assert data[0]["title"] == "C Task"
    assert data[1]["title"] == "B Task"
    assert data[2]["title"] == "A Task"

def test_fetch_deleted_tasks(client):
    # Create a task
    res = client.post("/api/v1/tasks", json={"title": "Task to delete"})
    task_id = res.json()["id"]
    
    # Delete the task (soft delete)
    version = res.json()["version"]
    client.delete(f"/api/v1/tasks/{task_id}?version={version}")
    
    # Default list should NOT include deleted task
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert all(task["id"] != task_id for task in data)
    
    # Requesting deleted tasks should include it
    response = client.get("/api/v1/tasks", params={"is_deleted": True})
    assert response.status_code == 200
    data = response.json()
    assert any(task["id"] == task_id for task in data)
    assert len(data) == 1
    assert data[0]["title"] == "Task to delete"

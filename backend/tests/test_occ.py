import pytest

def test_occ_conflict(client):
    # Fetch task
    task_resp = client.post("/api/v1/tasks", json={"title": "Task"})
    assert task_resp.status_code == 201
    task = task_resp.json()
    
    # User A updates
    # The first update should succeed and increment version to 2
    response_a = client.put(f"/api/v1/tasks/{task['id']}", json={**task, "title": "A", "version": 1})
    assert response_a.status_code == 200
    
    # User B updates with stale version (version 1, but it's now 2)
    response_b = client.put(f"/api/v1/tasks/{task['id']}", json={**task, "title": "B", "version": 1})
    assert response_b.status_code == 409

def test_delete_occ_conflict(client):
    task = client.post("/api/v1/tasks", json={"title": "Delete OCC Test"}).json()
    client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Updated", "version": task["version"]})
    response = client.delete(f"/api/v1/tasks/{task['id']}?version={task['version']}")
    assert response.status_code == 409

def test_put_occ_conflict(client, session):
    task = client.post("/api/v1/tasks", json={"title": "PUT OCC"}).json()
    # First update bumps version to 2
    client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Update 1", "version": task["version"]})
    # Second update with version 1 should fail with 409
    response = client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Update 2", "version": task["version"]})
    assert response.status_code == 409

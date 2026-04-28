def test_create_task(client):
    response = client.post("/api/v1/tasks", json={"title": "Test Task", "description": "Desc"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert "id" in data

def test_read_tasks(client):
    client.post("/api/v1/tasks", json={"title": "Task 1"})
    client.post("/api/v1/tasks", json={"title": "Task 2"})
    
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Task 1"
    assert data[1]["title"] == "Task 2"

def test_read_task(client):
    create_response = client.post("/api/v1/tasks", json={"title": "Single Task"})
    task_id = create_response.json()["id"]
    
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Single Task"

def test_update_task(client):
    create_response = client.post("/api/v1/tasks", json={"title": "Old Title"})
    task_id = create_response.json()["id"]
    version = create_response.json()["version"]
    
    response = client.put(f"/api/v1/tasks/{task_id}", json={"title": "New Title", "version": version})
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["version"] == 2

def test_delete_task(client):
    create_response = client.post("/api/v1/tasks", json={"title": "To be deleted"})
    task_id = create_response.json()["id"]
    version = create_response.json()["version"]
    
    response = client.delete(f"/api/v1/tasks/{task_id}?version={version}")
    assert response.status_code == 204
    
    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == 404

def test_complete_parent_unblocks_child(client):
    # Task A
    response_a = client.post("/api/v1/tasks", json={"title": "Task A"})
    task_a_id = response_a.json()["id"]
    
    # Task B (blocked by A)
    response_b = client.post("/api/v1/tasks", json={
        "title": "Task B",
        "dependency_ids": [task_a_id]
    })
    task_b_id = response_b.json()["id"]
    assert response_b.json()["is_blocked"] == True
    
    # Complete Task A
    response_patch = client.patch(f"/api/v1/tasks/{task_a_id}/status", json={
        "status": "Completed",
        "version": 1
    })
    assert response_patch.status_code == 200
    
    # Assert Task B is_blocked == False
    response_b_after = client.get(f"/api/v1/tasks/{task_b_id}")
    assert response_b_after.json()["is_blocked"] == False

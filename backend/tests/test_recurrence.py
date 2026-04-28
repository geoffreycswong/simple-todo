import pytest
from datetime import datetime, timedelta
from backend.app.recurrence import calculate_next_due_date

def test_calculate_next_due_date_due_date_anchor():
    # Weekly recurrence
    rule = "FREQ=WEEKLY;BYDAY=MO"
    current_due = datetime(2024, 4, 1, 10, 0) # A Monday
    
    next_due = calculate_next_due_date(rule, current_due, anchor="DUE_DATE")
    
    assert next_due == datetime(2024, 4, 8, 10, 0)

def test_calculate_next_due_date_completion_date_anchor():
    # Weekly recurrence from completion
    rule = "FREQ=WEEKLY"
    current_due = datetime(2024, 4, 1, 10, 0)
    completion_date = datetime(2024, 4, 3, 12, 0) # Wednesday
    
    next_due = calculate_next_due_date(rule, current_due, anchor="COMPLETION_DATE", completion_date=completion_date)
    
    # FREQ=WEEKLY from Wednesday 12:00 should be next Wednesday 12:00
    assert next_due == datetime(2024, 4, 10, 12, 0)

def test_recurring_task_creation_on_completion(client):
    # Create a recurring task
    due_date = (datetime.now() + timedelta(days=1)).isoformat()
    rule = "FREQ=DAILY"
    
    response = client.post("/api/v1/tasks", json={
        "title": "Daily Task",
        "due_date": due_date,
        "recurrence_rule": rule,
        "recurrence_anchor": "DUE_DATE"
    })
    assert response.status_code == 201
    task = response.json()
    task_id = task["id"]
    version = task["version"]
    
    # Complete the task
    patch_response = client.patch(f"/api/v1/tasks/{task_id}/status", json={
        "status": "Completed",
        "version": version
    })
    assert patch_response.status_code == 200
    
    # Check if a new task was created
    get_response = client.get("/api/v1/tasks")
    tasks = get_response.json()
    
    # Should have 2 tasks now: the completed one and the new one
    assert len(tasks) == 2
    
    new_tasks = [t for t in tasks if t["id"] != task_id]
    assert len(new_tasks) == 1
    new_task = new_tasks[0]
    
    assert new_task["title"] == "Daily Task"
    assert new_task["status"] == "Not Started"
    assert new_task["version"] == 1
    assert new_task["recurrence_rule"] == rule
    
    # Check due date of new task (should be 1 day after old due date)
    old_due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
    expected_due = old_due + timedelta(days=1)
    
    # The API might return different format, let's parse it
    new_due = datetime.fromisoformat(new_task["due_date"].replace("Z", "+00:00"))
    
    # Compare only up to seconds to avoid microsecond issues if any
    assert new_due.year == expected_due.year
    assert new_due.month == expected_due.month
    assert new_due.day == expected_due.day
    assert new_due.hour == expected_due.hour
    assert new_due.minute == expected_due.minute

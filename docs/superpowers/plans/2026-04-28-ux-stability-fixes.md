# TODO Application: Interaction & OCC Implementation Plan

**For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure edits trigger fresh state fetches, validate dependencies against deleted tasks, and enforce strict 409/404 OCC feedback loops across both frontend and backend.

### Task 1: Backend - Enforce Dependency Validity & Router OCC Handlers

**Files:**
- Modify: `backend/tests/test_occ.py`
- Modify: `backend/tests/test_dependencies.py`
- Modify: `backend/app/crud.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write TDD Tests for Backend Bug Fixes**
In `backend/tests/test_occ.py`, verify `PUT` OCC returns 409:
```python
def test_put_occ_conflict(client, db_session):
    task = client.post("/api/v1/tasks", json={"title": "PUT OCC"}).json()
    # First update bumps version to 2
    client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Update 1", "version": task["version"]})
    # Second update with version 1 should fail with 409
    response = client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Update 2", "version": task["version"]})
    assert response.status_code == 409
```
In `backend/tests/test_dependencies.py`, verify deleted tasks cannot be dependencies:
```python
def test_cannot_depend_on_deleted_task(client, db_session):
    t1 = client.post("/api/v1/tasks", json={"title": "Deleted Dep"}).json()
    client.delete(f"/api/v1/tasks/{t1['id']}?version={t1['version']}")
    
    # Try to create t2 depending on deleted t1
    response = client.post("/api/v1/tasks", json={"title": "Task 2", "dependency_ids": [t1['id']]})
    assert response.status_code == 400
```

- [ ] **Step 2: Prevent Linking to Deleted Tasks in `crud.py`**
In `backend/app/crud.py`, update `create_todo` and `update_todo` to validate `dependency_ids`:
```python
from fastapi import HTTPException

# Inside create_todo:
if todo.dependency_ids:
    prerequisites = db.query(models.Todo).filter(
        models.Todo.id.in_(todo.dependency_ids), 
        models.Todo.deleted_at == None # MUST be active
    ).all()
    if len(prerequisites) != len(todo.dependency_ids):
        raise HTTPException(status_code=400, detail="One or more dependencies do not exist or are deleted")
    db_todo.prerequisites = prerequisites
    db_todo.is_blocked = any(p.status != "Completed" for p in prerequisites)

# Inside update_todo (where dependency_ids are handled):
if "dependency_ids" in update_data:
    dep_ids = update_data["dependency_ids"]
    if dep_ids is not None:
        prerequisites = db.query(models.Todo).filter(
            models.Todo.id.in_(dep_ids),
            models.Todo.deleted_at == None # MUST be active
        ).all()
        if len(prerequisites) != len(dep_ids):
            raise HTTPException(status_code=400, detail="One or more dependencies do not exist or are deleted")
        db_todo.prerequisites = prerequisites
    else:
        db_todo.prerequisites = []
```

- [ ] **Step 3: Catch VersionMismatchError in `main.py`**
Ensure the `PUT` and `PATCH` routes in `backend/app/main.py` explicitly catch the OCC error:
```python
@app.put("/api/v1/tasks/{task_id}", response_model=schemas.Todo)
def update_task(task_id: uuid.UUID, todo: schemas.TodoUpdate, db: Session = Depends(get_db)):
    try:
        updated_todo = crud.update_todo(db=db, todo_id=task_id, todo=todo)
        if updated_todo is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return updated_todo
    except crud.VersionMismatchError as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.patch("/api/v1/tasks/{task_id}/status", response_model=schemas.Todo)
def update_task_status(task_id: uuid.UUID, status_update: schemas.TodoStatusUpdate, db: Session = Depends(get_db)):
    try:
        # Same try/except block catching crud.VersionMismatchError
        # ...
```

- [ ] **Step 4: Run tests and commit**
Run: `pytest backend/tests/`
Commit: `git add backend/ && git commit -m "fix(backend): validate dependencies against deleted tasks and enforce 409 OCC on PUT/PATCH"`

---

### Task 2: Frontend - Handle 404 Deletions & OCC Fallbacks

**Files:**
- Modify: `frontend/src/composables/useTasks.ts`

- [ ] **Step 1: Add 404 Handling to `useTasks.ts`**
Update `updateTaskStatus`, `updateTaskDetails`, and `deleteTask` to catch 404 errors (which occur when the user interacts with a task another user just deleted) and alert the user.
```typescript
  // Inside updateTaskDetails (apply similar logic to updateTaskStatus and deleteTask):
  const updateTaskDetails = async (id: string, payload: any, version: number) => {
    try {
      await apiClient(`/tasks/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ ...payload, version })
      })
      await fetchTasks()
    } catch (e: any) {
      if (e instanceof ApiError && (e.status === 409 || e.status === 404)) {
        await fetchTasks() // Reconcile state
        const msg = e.status === 404 
          ? "Error: This task has been deleted by someone else." 
          : "Conflict: This task was modified by someone else.";
        window.alert(`${msg} Your view has been updated.`)
        error.value = e.message
      } else if (e instanceof ApiError && e.status === 422) {
        await fetchTasks()
        error.value = e.message
      }
      throw e
    }
  }
```

- [ ] **Step 2: Commit**
Commit: `git add frontend/ && git commit -m "fix(frontend): add 404 handling to OCC logic to prevent silent errors on deleted tasks"`

---

### Task 3: Frontend - Refresh State on "Edit" Click

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Update `openEditTaskModal` logic**
Change the `openEditTaskModal` function to be `async`. It must fetch the latest dependencies and the latest task list to guarantee the user is editing the freshest state and cannot select stale dependencies.
```vue
<script setup lang="ts">
// ... existing imports

const openEditTaskModal = async (task: any) => {
  try {
    // 1. Refresh dependencies so deleted tasks drop off the dropdown list
    await fetchAllTaskOptions()
    
    // 2. Refresh the main task list to ensure we have the latest version of the task
    await fetchTasks()
    
    // 3. Find the freshest version of the task to edit
    const freshestTask = tasks.value.find(t => t.id === task.id)
    
    if (!freshestTask) {
      window.alert("This task has been deleted and cannot be edited.")
      return
    }
    
    taskToEdit.value = freshestTask
    isModalOpen.value = true
  } catch (error) {
    console.error("Failed to prepare edit modal:", error)
  }
}
</script>
```

- [ ] **Step 2: Commit**
Commit: `git add frontend/ && git commit -m "fix(frontend): force state refresh when opening edit modal to prevent stale dependencies and versions"`
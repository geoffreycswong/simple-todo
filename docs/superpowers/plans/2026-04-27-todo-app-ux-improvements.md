# TODO Application: Bug Fix Implementation Plan

**For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Patch state synchronization bugs, OCC alert handling, soft-delete visibility, UI sorting omissions, and dependency update logic in the Vue 3 + FastAPI TODO application.

---

### Task 1: Post-Creation Dependency Editing

**Files:**
- Modify: `backend/tests/test_dependencies.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/crud.py`

- [ ] **Step 1: Write failing TDD test for updating dependencies**
In `backend/tests/test_dependencies.py`, add a test:
```python
def test_update_task_dependencies(client, db_session):
    # Create two independent tasks
    t1 = client.post("/api/v1/tasks", json={"title": "Task 1"}).json()
    t2 = client.post("/api/v1/tasks", json={"title": "Task 2"}).json()
    
    # Update t2 to depend on t1
    response = client.put(f"/api/v1/tasks/{t2['id']}", json={
        "title": "Task 2",
        "version": t2["version"],
        "dependency_ids": [t1['id']]
    })
    assert response.status_code == 200
    assert response.json()["is_blocked"] == True
```

- [ ] **Step 2: Update `TodoUpdate` schema**
In `backend/app/schemas.py`, add `dependency_ids` to `TodoUpdate`:
```python
from typing import List, Optional
import uuid
from pydantic import BaseModel
from datetime import datetime

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    recurrence_rule: Optional[str] = None
    recurrence_anchor: Optional[str] = None
    dependency_ids: Optional[List[uuid.UUID]] = None # Added for Bug 5
    version: int
```

- [ ] **Step 3: Update `crud.update_todo` to handle relationships**
In `backend/app/crud.py`, modify `update_todo` to intercept `dependency_ids`:
```python
def update_todo(db: Session, todo_id: uuid.UUID, todo_update: schemas.TodoUpdate):
    db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not db_todo:
        return None
    if db_todo.version != todo_update.version:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Version mismatch")

    update_data = todo_update.dict(exclude_unset=True)
    
    # Handle dependency_ids relationship update
    if "dependency_ids" in update_data:
        dep_ids = update_data.pop("dependency_ids")
        if dep_ids is not None:
            prerequisites = db.query(models.Todo).filter(models.Todo.id.in_(dep_ids)).all()
            db_todo.prerequisites = prerequisites
            # Recalculate is_blocked dynamically
            db_todo.is_blocked = any(p.status != "Completed" for p in prerequisites)

    for key, value in update_data.items():
        if key != "version":
            setattr(db_todo, key, value)

    db_todo.version += 1
    db_todo.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_todo)
    return db_todo
```

- [ ] **Step 4: Run backend tests and commit**
Run: `pytest backend/tests/test_dependencies.py` (Expected: PASS)
Commit: `git add backend/ && git commit -m "fix(backend): allow updating dependency_ids on existing tasks"`

---

### Task 2: Soft Delete Visibility

**Files:**
- Modify: `backend/tests/test_filtering.py`
- Modify: `backend/app/crud.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing TDD test for fetching deleted tasks**
In `backend/tests/test_filtering.py`, add:
```python
def test_fetch_deleted_tasks(client, db_session):
    task = client.post("/api/v1/tasks", json={"title": "To Delete"}).json()
    client.delete(f"/api/v1/tasks/{task['id']}")
    
    # Standard fetch should hide it
    res_active = client.get("/api/v1/tasks").json()
    assert len([t for t in res_active if t['id'] == task['id']]) == 0
    
    # Fetch with is_deleted=true should reveal it
    res_deleted = client.get("/api/v1/tasks?is_deleted=true").json()
    assert len([t for t in res_deleted if t['id'] == task['id']]) == 1
```

- [ ] **Step 2: Update `crud.py` query logic**
In `backend/app/crud.py`, modify both `get_todos` and `count_todos`:
```python
# Replace the hardcoded .filter(models.Todo.deleted_at == None)
# Add parameter: is_deleted: Optional[bool] = False
def get_todos(..., is_deleted: Optional[bool] = False):
    query = db.query(models.Todo)
    if is_deleted:
        query = query.filter(models.Todo.deleted_at != None)
    else:
        query = query.filter(models.Todo.deleted_at == None)
    # ... rest of existing filters
```
*(Apply the exact same `if/else` logic block for `count_todos`)*.

- [ ] **Step 3: Expose `is_deleted` in `main.py`**
In `backend/app/main.py`, update `read_tasks`:
```python
@app.get("/api/v1/tasks", response_model=List[schemas.Todo])
def read_tasks(
    # ... existing params
    due_date_after: Optional[datetime] = None,
    is_deleted: Optional[bool] = False, # Added parameter
    sort_by: Optional[str] = None,
    # ...
):
    total = crud.count_todos(..., is_deleted=is_deleted)
    tasks = crud.get_todos(..., is_deleted=is_deleted, sort_by=sort_by, order=order)
```

- [ ] **Step 4: Run tests and commit**
Run: `pytest backend/tests/test_filtering.py` (Expected: PASS)
Commit: `git add backend/ && git commit -m "fix(backend): add is_deleted filter parameter to reveal soft deletes"`

---

### Task 3: Singleton State Synchronization

**Files:**
- Modify: `frontend/src/composables/useTasks.ts`

- [ ] **Step 1: Refactor `useTasks.ts` to use a global singleton pattern**
Move the reactive references OUTSIDE the `export function useTasks()` block so they are shared across components. Add a `currentParams` object to hold active filters and ensure we **overwrite** it when new params are passed, preventing the "Sticky Filter" bug.

```typescript
import { ref } from 'vue'
import { apiClient, ApiError } from '../services/api'

// GLOBAL STATE (Singleton)
const tasks = ref<any[]>([])
const totalTasks = ref(0)
const allTaskOptions = ref<any[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const currentParams = ref<any>({}) // Stores active filters & pagination

export function useTasks() {
  const fetchTasks = async (params?: any) => {
    isLoading.value = true
    error.value = null
    
    // OVERWRITE entirely instead of merging, so cleared filters are actually removed
    if (params) {
      currentParams.value = params 
    }
    
    try {
      const queryString = new URLSearchParams(currentParams.value).toString()
      const { data, total } = await apiClient<any[]>('/tasks' + (queryString ? '?' + queryString : ''))
      tasks.value = data
      if (total !== undefined) totalTasks.value = total
    } catch (e: any) {
      error.value = e.message
    } finally {
      isLoading.value = false
    }
  }
  
  // Note: Keep updateTaskStatus, updateTaskDetails, deleteTask, fetchAllTaskOptions 
  // exactly as they are currently implemented inside the function.
  
  return { 
    tasks, totalTasks, allTaskOptions, isLoading, error, 
    fetchTasks, /* return other functions here */ 
  }
}
```

- [ ] **Step 2: Commit**
Commit: `git add frontend/src/composables/useTasks.ts && git commit -m "fix(frontend): convert useTasks state to singleton and fix filter clearing"`

---

### Task 4: Explicit OCC Alerts

**Files:**
- Modify: `frontend/src/composables/__tests__/useTasks.spec.ts`
- Modify: `frontend/src/composables/useTasks.ts`

- [ ] **Step 1: Add TDD test for window.alert on 409**
In `useTasks.spec.ts`, mock the `window.alert` function:
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
// ... existing imports

describe('useTasks OCC', () => {
  it('triggers window.alert on 409 conflict and refreshes', async () => {
    const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {})
    vi.mocked(api.apiClient).mockRejectedValue(new api.ApiError(409, "Version mismatch"))
    
    const { updateTaskStatus } = useTasks()
    
    // Expect error to be thrown so components can catch it, but alert is handled internally
    await expect(updateTaskStatus('1', 'Completed', 1)).rejects.toThrow()
    expect(alertMock).toHaveBeenCalledWith(expect.stringContaining("modified by someone else"))
    
    alertMock.mockRestore()
  })
})
```

- [ ] **Step 2: Implement `window.alert` in `useTasks.ts`**
Update `updateTaskStatus` and `updateTaskDetails` in `useTasks.ts` to include the explicit alert:
```typescript
  const updateTaskStatus = async (id: string, status: string, version: number) => {
    try {
      await apiClient(`/tasks/${id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, version })
      })
      await fetchTasks() 
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 409) {
        window.alert("Conflict: This task was modified by someone else. The list will now refresh to show the latest version.")
        await fetchTasks() // Reconcile
      } else if (e instanceof ApiError && e.status === 422) {
        error.value = e.message // Just show dependency error in UI without alert
      }
      throw e
    }
  }

  const updateTaskDetails = async (id: string, payload: any, version: number) => {
    try {
      await apiClient(`/tasks/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ ...payload, version })
      })
      await fetchTasks()
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 409) {
        window.alert("Conflict: This task was modified by someone else. Your changes could not be saved. The list will now refresh.")
        await fetchTasks() // Reconcile
      }
      throw e // Keep throwing so the UI doesn't incorrectly close the modal
    }
  }
```

- [ ] **Step 3: Run frontend tests and commit**
Run: `npm run test` (Expected: PASS)
Commit: `git add frontend/ && git commit -m "fix(frontend): add explicit window.alert for 409 OCC collisions"`

---

### Task 5: FilterBar Sorting & Soft Delete UI

**Files:**
- Modify: `frontend/src/components/FilterBar.vue`

- [ ] **Step 1: Expand `FilterBar.vue` UI controls**
```vue
<script setup lang="ts">
import { reactive, watch } from 'vue'

const emit = defineEmits(['filter'])
const filters = reactive({ 
  status: '', priority: '', is_blocked: '', 
  is_deleted: '', sort_by: 'due_date', order: 'asc' // Added sorting and deleted state
})

watch(filters, (newFilters) => {
  const payload = Object.fromEntries(Object.entries(newFilters).filter(([_, v]) => v !== ''))
  emit('filter', payload)
}, { deep: true })
</script>

<template>
  <div class="p-4 bg-gray-100 rounded flex flex-wrap gap-4 mb-6 items-center">
    <select v-model="filters.status" class="p-2 border rounded bg-white text-sm">
      <option value="">All Statuses</option>
      <option value="Not Started">Not Started</option>
      <option value="In Progress">In Progress</option>
      <option value="Completed">Completed</option>
    </select>
    <select v-model="filters.priority" class="p-2 border rounded bg-white text-sm">
      <option value="">All Priorities</option>
      <option value="Low">Low</option>
      <option value="Medium">Medium</option>
      <option value="High">High</option>
    </select>
    <select v-model="filters.is_blocked" class="p-2 border rounded bg-white text-sm">
      <option value="">All Dependency States</option>
      <option :value="true">Blocked</option>
      <option :value="false">Unblocked</option>
    </select>
    
    <select v-model="filters.is_deleted" class="p-2 border rounded bg-white text-sm">
      <option value="">Active Tasks</option>
      <option :value="true">Show Deleted Tasks</option>
    </select>

    <div class="w-px h-8 bg-gray-300 mx-2"></div> <span class="text-sm font-bold text-gray-500 uppercase">Sort:</span>
    <select v-model="filters.sort_by" class="p-2 border rounded bg-white text-sm">
      <option value="due_date">Due Date</option>
      <option value="priority">Priority</option>
      <option value="status">Status</option>
      <option value="title">Name</option>
    </select>
    <select v-model="filters.order" class="p-2 border rounded bg-white text-sm">
      <option value="asc">Ascending</option>
      <option value="desc">Descending</option>
    </select>
  </div>
</template>
```

- [ ] **Step 2: Verify and Commit**
Start the frontend server (`npm run dev`) and visually confirm the new FilterBar controls map directly to the URL query parameters sent to the backend.
Commit: `git add frontend/ && git commit -m "fix(frontend): add sorting controls and soft-delete toggle to FilterBar"`
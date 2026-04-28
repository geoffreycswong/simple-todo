# TODO Application MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a robust, concurrent TODO application with task dependencies and recurring schedules.

**Architecture:** Stateless FastAPI backend using SQLAlchemy (PostgreSQL) with Optimistic Concurrency Control (OCC). Background tasks handle dependency propagation and recurrence generation.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL 15, Alembic, Pytest, Docker Compose, Terraform.

---

### Task 1: Project Initialization & Docker Setup

**Files:**
- Create: `projects/example-todo-app/backend/app/main.py`
- Create: `projects/example-todo-app/backend/requirements.txt`
- Create: `projects/example-todo-app/Dockerfile`
- Create: `projects/example-todo-app/docker-compose.yml`
- Create: `projects/example-todo-app/.env.example`

- [ ] **Step 1: Create requirements.txt**
```text
fastapi==0.110.0
uvicorn==0.27.1
sqlalchemy==2.0.27
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic==2.6.3
pydantic-settings==2.2.1
python-dateutil==2.8.2
tenacity==8.2.3
pytest==8.0.2
httpx==0.27.0
```

- [ ] **Step 2: Create Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
ENV PYTHONPATH=/app
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 3: Create docker-compose.yml**
```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: todo_db
    ports:
      - "5432:5432"
  api:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./backend:/app/backend
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/todo_db
      APP_ENV: local
    ports:
      - "8000:8000"
    depends_on:
      - db
```

- [ ] **Step 4: Create a minimal FastAPI app**
```python
from fastapi import FastAPI

app = FastAPI(title="TODO API")

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 5: Verify setup**
Run: `docker-compose up -d --build && curl http://localhost:8000/health`
Expected: `{"status": "ok"}`

- [ ] **Step 6: Commit**
```bash
git add projects/example-todo-app/backend/app/main.py projects/example-todo-app/backend/requirements.txt projects/example-todo-app/Dockerfile projects/example-todo-app/docker-compose.yml
git commit -m "feat: project initialization with docker setup"
```

---

### Task 2: Database Schema & Alembic Initialization

**Files:**
- Create: `projects/example-todo-app/backend/app/database.py`
- Create: `projects/example-todo-app/backend/app/models.py`
- Create: `projects/example-todo-app/backend/alembic.ini`
- Create: `projects/example-todo-app/backend/migrations/env.py`

- [ ] **Step 1: Setup database connection**
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/todo_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
```

- [ ] **Step 2: Define Models**
```python
import uuid
from sqlalchemy import Column, String, Text, DateTime, Enum, Boolean, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

class Todo(Base):
    __tablename__ = "todos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Not Started", index=True)
    priority = Column(String(50), nullable=False, default="Medium", index=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    recurrence_rule = Column(String(255), nullable=True)
    recurrence_anchor = Column(String(50), default="DUE_DATE")
    is_blocked = Column(Boolean, nullable=False, default=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    dependent_task_id = Column(UUID(as_uuid=True), ForeignKey("todos.id"), primary_key=True)
    prerequisite_task_id = Column(UUID(as_uuid=True), ForeignKey("todos.id"), primary_key=True)
```

- [ ] **Step 3: Initialize Alembic**
Run: `docker-compose exec api alembic init migrations` (locally: `cd projects/example-todo-app/backend && alembic init migrations`)

- [ ] **Step 4: Configure Alembic env.py to use Base.metadata**

- [ ] **Step 5: Generate and run first migration**
Run: `docker-compose exec api alembic revision --autogenerate -m "initial_schema" && docker-compose exec api alembic upgrade head`

- [ ] **Step 6: Commit**
```bash
git add projects/example-todo-app/backend/app/database.py projects/example-todo-app/backend/app/models.py projects/example-todo-app/backend/alembic.ini
git commit -m "feat: database schema and alembic initialization"
```

---

### Task 3: CRUD API - Basic Operations (TDD)

**Files:**
- Create: `projects/example-todo-app/backend/app/schemas.py`
- Create: `projects/example-todo-app/backend/app/crud.py`
- Modify: `projects/example-todo-app/backend/app/main.py`
- Create: `projects/example-todo-app/backend/tests/test_api.py`

- [ ] **Step 1: Write failing test for task creation**
```python
def test_create_task(client):
    response = client.post("/api/v1/tasks", json={"title": "Test Task", "description": "Desc"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert "id" in data
```

- [ ] **Step 2: Run test (Expect FAIL)**

- [ ] **Step 3: Implement schemas, CRUD, and endpoint**
(Detailed code for Task, TodoCreate, TodoUpdate schemas and FastAPI router)

- [ ] **Step 4: Run test (Expect PASS)**

- [ ] **Step 5: Repeat for GET, PUT, DELETE**

- [ ] **Step 6: Commit**

---

### Task 4: Optimistic Concurrency Control (OCC) Implementation

**Files:**
- Modify: `projects/example-todo-app/backend/app/crud.py`
- Modify: `projects/example-todo-app/backend/app/main.py`
- Create: `projects/example-todo-app/backend/tests/test_occ.py`

- [ ] **Step 1: Write failing test for OCC conflict**
```python
def test_occ_conflict(client):
    # Fetch task
    task = client.post("/api/v1/tasks", json={"title": "Task"}).json()
    # User A updates
    client.put(f"/api/v1/tasks/{task['id']}", json={**task, "title": "A", "version": 1})
    # User B updates with stale version
    response = client.put(f"/api/v1/tasks/{task['id']}", json={**task, "title": "B", "version": 1})
    assert response.status_code == 409
```

- [ ] **Step 2: Run test (Expect FAIL)**

- [ ] **Step 3: Implement OCC check in CRUD/Update logic**
```python
# snippet
if db_todo.version != todo.version:
    raise StaleDataError()
db_todo.version += 1
```

- [ ] **Step 4: Run test (Expect PASS)**

- [ ] **Step 5: Commit**

---

### Task 5: Task Dependencies & Blocking Logic

**Files:**
- Modify: `projects/example-todo-app/backend/app/crud.py`
- Modify: `projects/example-todo-app/backend/app/main.py`
- Create: `projects/example-todo-app/backend/tests/test_dependencies.py`

- [ ] **Step 1: Write failing test for blocked task transition**
```python
def test_start_blocked_task_fails(client):
    # Create Task A (parent), Task B (child depending on A)
    # Set Task B.is_blocked = True
    # Attempt PATCH /api/v1/tasks/B/status json={"status": "In Progress"}
    # Assert 422
```

- [ ] **Step 2: Implement dependency validation in PATCH status endpoint**

- [ ] **Step 3: Implement "Momentum Rule" (already In Progress tasks stay In Progress)**

- [ ] **Step 4: Run tests and verify**

- [ ] **Step 5: Commit**

---

### Task 6: Recurring Tasks Implementation

**Files:**
- Create: `projects/example-todo-app/backend/app/recurrence.py`
- Modify: `projects/example-todo-app/backend/app/main.py`
- Create: `projects/example-todo-app/backend/tests/test_recurrence.py`

- [ ] **Step 1: Write tests for DUE_DATE and COMPLETION_DATE anchors**
(Validate using `dateutil.rrule`)

- [ ] **Step 2: Implement recurrence generator hook in status change to 'Completed'**

- [ ] **Step 3: Verify next task creation on completion**

- [ ] **Step 4: Commit**

---

### Task 7: Dependency Propagation (Background Tasks & Retries)

**Files:**
- Create: `projects/example-todo-app/backend/app/background.py`
- Modify: `projects/example-todo-app/backend/app/main.py`

- [ ] **Step 1: Write test for downstream unblocking**
```python
def test_complete_parent_unblocks_child(client):
    # Task A -> Task B (blocked)
    # Complete Task A
    # Assert Task B is_blocked == False
```

- [ ] **Step 2: Implement FastAPI BackgroundTask for propagation**

- [ ] **Step 3: Implement Tenacity retry loop for OCC collisions in background task**

- [ ] **Step 4: Commit**

---

### Task 8: Filtering & Sorting

- [ ] **Step 1: Implement query parameters in GET /tasks** (status, priority, is_blocked, due_date)
- [ ] **Step 2: Implement sorting logic**
- [ ] **Step 3: Commit**

---

### Task 9: Infrastructure (Terraform)

**Files:**
- Create: `projects/example-todo-app/terraform/main.tf`
- Create: `projects/example-todo-app/terraform/variables.tf`

- [ ] **Step 1: Define Google Provider and Cloud SQL instance**
- [ ] **Step 2: Define Artifact Registry and Cloud Run service**
- [ ] **Step 3: Commit**

---

### Task 10: Simple Web UI

- [ ] **Step 1: Create a simple index.html using Tailwind CDN and Vanilla JS**
- [ ] **Step 2: Implement fetching and displaying tasks**
- [ ] **Step 3: Implement creating and completing tasks**
- [ ] **Step 4: Commit**

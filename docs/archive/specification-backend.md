# TODO Application: Backend & Infrastructure Engineering Specification

## 1. Engineering Philosophy & Architecture Baseline
This specification outlines the backend and infrastructure implementation for a highly concurrent, multi-user TODO application. To maintain our operational focus strictly at the platform and service layers—excluding core infrastructure maintenance—the production architecture relies entirely on managed, stateless, and serverless components. 

The application utilizes **Python (FastAPI)**, **SQLAlchemy (PostgreSQL)**, and **Alembic** for migrations. We enforce **Test-Driven Development (TDD)**; failing tests must be written for all API contracts and edge cases before implementing the business logic.

---

## 2. Database Schema (SQLAlchemy / PostgreSQL)
Initialize the database using Alembic migrations. The schema is normalized for high-concurrency read operations.

### Table: `todos`
* `id`: `UUID` (Primary Key, auto-generated)
* `title`: `VARCHAR(255)` (Not Null, Indexed)
* `description`: `TEXT` (Nullable)
* `status`: `VARCHAR(50)` (Enum: 'Not Started', 'In Progress', 'Completed', 'Archived') (Not Null, Default: 'Not Started', Indexed)
* `priority`: `VARCHAR(50)` (Enum: 'Low', 'Medium', 'High') (Not Null, Default: 'Medium', Indexed)
* `due_date`: `TIMESTAMP WITH TIME ZONE` (Nullable, Indexed)
* `recurrence_rule`: `VARCHAR(255)` (Nullable) - Stores standard RFC 5545 RRULE strings.
* `recurrence_anchor`: `VARCHAR(50)` (Enum: 'DUE_DATE', 'COMPLETION_DATE') (Default: 'DUE_DATE')
* `is_blocked`: `BOOLEAN` (Not Null, Default: False, Indexed) - System-managed denormalized flag.
* `version`: `INTEGER` (Not Null, Default: 1) - Used for Optimistic Concurrency Control (OCC).
* `created_at`, `updated_at`: `TIMESTAMP WITH TIME ZONE` (Defaults: `NOW()`)
* `deleted_at`: `TIMESTAMP WITH TIME ZONE` (Nullable, Heavily Indexed for soft-delete filtering)

### Table: `task_dependencies` (Junction Table)
* `dependent_task_id`: `UUID` (Foreign Key -> `todos.id`, Not Null, Indexed)
* `prerequisite_task_id`: `UUID` (Foreign Key -> `todos.id`, Not Null, Indexed)
* *Constraint:* Composite Primary Key on `(dependent_task_id, prerequisite_task_id)`.

---

## 3. API Contracts & Pydantic Schemas (FastAPI)
All endpoints must consume and produce `application/json`. 

**Critical Payload Isolation Rule:** Client payloads must **never** be allowed to dictate or update the `is_blocked` flag. The Pydantic update schemas must explicitly exclude or strip this field to prevent clients from overwriting system-calculated dependency states.

* **`POST /api/v1/tasks`**: Accepts standard task fields and an optional array of `dependency_ids`. Sets `version: 1`. 
* **`GET /api/v1/tasks`**: Returns a list of tasks. 
    * *Mandatory Filter:* Must automatically append `WHERE deleted_at IS NULL` and `WHERE status != 'Archived'` unless `status=Archived` is explicitly requested.
    * *Supported Query Params:* `status`, `priority`, `due_date_before`, `due_date_after`, `is_blocked`.
    * *Sorting:* Support `sort_by` and `order` (asc/desc).
* **`GET /api/v1/tasks/{id}`**: Returns task details, including `version` and an array of its `dependency_ids`.
* **`PUT /api/v1/tasks/{id}`**: Full update. **Must include `version` in payload.**
    * *OCC Logic:* Backend compares payload `version` with DB `version`. If mismatch, return `409 Conflict`. If match, perform update and increment DB `version` by 1.
* **`PATCH /api/v1/tasks/{id}/status`**: Dedicated state transition endpoint. Accepts `status` and `version`. Triggers business logic hooks (see Section 4).
* **`DELETE /api/v1/tasks/{id}`**: Soft delete. Sets `deleted_at = NOW()`. Returns `204 No Content`.

---

## 4. Business Logic & Asynchronous Hooks

### A. The Dependency State Machine (Conditional Lock)
When the `PATCH` endpoint is called to change a task's status to `In Progress`:
1.  Check the `is_blocked` flag. 
2.  If `is_blocked == true`, reject with `422 Unprocessable Entity` ("Prerequisites not completed").
3.  *Momentum Rule:* This lock *only* applies when transitioning *into* `In Progress`. If a task is already `In Progress`, and a prerequisite is reverted to `Not Started`, the current task remains `In Progress`.

### B. The Recurrence Generator (Procedural Hook)
When a task's status changes to `Completed`, check if `recurrence_rule` is populated. If true:
1.  Generate a new `due_date` using the `dateutil.rrule` library.
2.  If `recurrence_anchor` is `DUE_DATE`, calculate the next interval from the old task's `due_date`. If `COMPLETION_DATE`, calculate from `NOW()`.
3.  Execute an `INSERT` for a new task clone with the calculated `due_date`, `status: 'Not Started'`, and `version: 1`. Commit within the same transaction.

### C. The Unblock Propagator (Background Task & Retry Loop)
When a task's status changes to `Completed`, trigger a FastAPI `BackgroundTask` to update downstream dependencies.
1.  Query `task_dependencies` to find all tasks where `prerequisite_task_id` equals the completed task.
2.  For each dependent task, verify if *all* its prerequisites are now completed.
3.  If yes, set `is_blocked = false`.
4.  **OCC Collision Protection:** Wrap this database commit in a `tenacity` retry loop. If SQLAlchemy throws a `StaleDataError` (meaning a user edited the task at the exact same millisecond), the loop must re-fetch the latest `version` from the DB, re-apply `is_blocked = false`, and attempt the commit again.

---

## 5. TDD Strategy (Pytest Requirements)
Before implementing the endpoints, write the following test suites using a mock database session:
* **OCC Suite:** Simulate concurrent `PUT` requests. Assert that the first succeeds and the second receives a `409 Conflict`.
* **State Transition Suite:** * Attempt to start a blocked task (Expect 422).
    * Start an unblocked task (Expect 200).
    * Revert a parent task while the child is 'In Progress', then complete the child (Expect 200 - testing the conditional lock momentum).
* **Recurrence Suite:** Validate next-date calculation for both `DUE_DATE` and `COMPLETION_DATE` anchors using a standard weekly RRULE.
* **Race Condition Suite:** Mock an OCC `StaleDataError` during the background propagation hook and assert that the `tenacity` retry loop successfully recovers and updates the `is_blocked` flag.

---

## 6. Infrastructure & Deployment Setup
The application utilizes a 12-Factor approach driven entirely by environment variables (specifically `DATABASE_URL` and `APP_ENV` via `pydantic-settings`).

### Local Environment (Docker Compose)
* Provide a `docker-compose.yml` containing a `postgres:15-alpine` service and a FastAPI `api` service.
* The `api` service must bind-mount the local source code directory for hot-reloading (`uvicorn --reload`).
* Include an Alembic startup script in the container entrypoint to auto-migrate the local DB on boot.

### Production Environment (Terraform on GCP)
* Provide `main.tf` configuring:
    * `google_sql_database_instance` (Postgres 15, private IP).
    * `google_artifact_registry_repository` (Docker format).
    * `google_cloud_run_v2_service` (Deploying the image, injecting `DATABASE_URL` securely, handling HTTP concurrency and scaling).
* The Dockerfile entrypoint must explicitly run `alembic upgrade head` before starting the Uvicorn worker to ensure cloud database schemas are in sync prior to accepting traffic.
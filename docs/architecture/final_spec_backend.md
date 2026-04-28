# SimpleTodo Backend: Final Engineering Specification (As-Built)

## 1. Engineering Philosophy & Core Stack
The backend is a robust, RESTful API designed to support high-concurrency environments while maintaining strict data integrity. It utilizes a denormalized read-path for high performance and an Optimistic Concurrency Control (OCC) write-path to prevent race conditions.

**Core Stack:** FastAPI (Python 3.11+), SQLAlchemy 2.0, PostgreSQL (Production) / SQLite (Testing), Alembic.

## 2. Data Model & Database Schema
The primary entity is the `Todo` model. 
* **Concurrency:** Managed via a `version` integer column.
* **Soft Deletes:** Managed via a `deleted_at` timestamp.
* **Dependencies:** Managed via a many-to-many self-referential table (`todo_dependencies`).
* **Performance:** The `is_blocked` boolean is a denormalized field calculated dynamically during write operations to ensure `GET` requests remain fast.

## 3. API Contract & Routing

### `GET /api/v1/tasks` (List & Filter)
* **Pagination:** Query params `skip` and `limit`. The total count of matched records is returned in the `X-Total-Count` HTTP Response Header.
* **Filters:** `status`, `priority`, `is_blocked`, `due_date_before`, `due_date_after`.
* **Visibility:** Accepts `is_deleted` (boolean). If false (default), strictly filters where `deleted_at == None`.
* **Sorting:** `sort_by` (due_date, priority, status, title) and `order` (asc, desc).

### `POST /api/v1/tasks` (Create)
* Accepts a `TodoCreate` schema. 
* Can accept `dependency_ids`. The backend validates that all requested dependencies exist and are *not* soft-deleted, throwing a `400 Bad Request` if invalid.

### `PUT /api/v1/tasks/{id}` (Update Details)
* Accepts a `TodoUpdate` schema, which **must include the `version` integer**.
* **Dependency Updates:** Accepts an updated array of `dependency_ids`. The backend dynamically links the new prerequisites and recalculates the `is_blocked` flag based on the completion status of the new parents.

### `PATCH /api/v1/tasks/{id}/status` (Update Status)
* Accepts a `TodoStatusUpdate` schema (status and **version**).
* If a task transitions to "Completed", a background task (`background.py`) is spawned to find all downstream dependent tasks and unblock them (recalculating their `is_blocked` flag).

### `DELETE /api/v1/tasks/{id}` (Soft Delete)
* **OCC Protected:** Mandates `version` as a query parameter (e.g., `?version=X`).
* Populates the `deleted_at` timestamp instead of destroying the row.

## 4. Core Business Logic & Protections

### Optimistic Concurrency Control (OCC)
All mutating operations (`PUT`, `PATCH`, `DELETE`) are protected by OCC.
1. The backend compares the incoming `version` against the database row.
2. If they mismatch, the router catches the `crud.VersionMismatchError` and throws an `HTTP 409 Conflict`.
3. If the task was already soft-deleted by another user, `crud.py` returns `None`, and the router throws an `HTTP 404 Not Found`.

### State Propagation
To ensure the `is_blocked` flag remains a reliable source of truth, the backend actively intercepts dependency updates. A task cannot depend on a deleted task, and attempting to do so will reject the transaction.
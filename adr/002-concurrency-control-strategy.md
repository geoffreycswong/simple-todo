# ADR 002: Concurrency Control Strategy

**Status:** Approved (Amended post-MVP iteration)

**Context:**
The application must support multiple users concurrently accessing and modifying the same TODO list. A mechanism is required to ensure data consistency during simultaneous updates without locking the UI or degrading the user experience. During the initial implementation, concurrency control was focused on state modifications (`PUT` and `PATCH`). However, testing revealed a critical race condition where destructive operations (`DELETE`) could silently overwrite concurrent user edits, necessitating an expansion of the concurrency strategy.

**Requirements:**
* Prevent "lost updates" when two users edit the same task simultaneously.
* Prevent silent data loss when one user deletes a task while another is actively editing it.
* Ensure high availability and a frictionless user experience (no UI freezes or hard database locks during editing).
* Maintain strict transactional consistency at the row level across all write and destructive operations.

**Technical Constraints & Exploration:**
Pessimistic locking (locking the database row as soon as a user opens the edit screen) guarantees consistency but creates a fragile user experience; if a user opens a task and leaves their session idle, all other users are blocked from modifying it. Eventual consistency resolves the locking issue but risks silent data overwrites, violating the core reliability requirements of a shared list. 

Furthermore, enforcing concurrency on `DELETE` operations presented a REST architecture constraint: HTTP `DELETE` requests conventionally do not (and often cannot) reliably pass JSON bodies. Therefore, the concurrency token for deletions must be handled differently than standard payload updates.

**Decision (Detailed Architecture):**
We implemented **Optimistic Concurrency Control (OCC)** globally across all mutating operations using a `version` integer column on the `todos` table.

* **The Lock:** When a client fetches a task, it receives the current `version`. Any state mutation must provide this version back to the server.
* **Standard Updates (`PUT`, `PATCH`):** The `version` is included in the JSON payload. The backend validates it against the database. If it matches, the transaction commits and increments the version by 1. 
* **Destructive Operations (`DELETE`):** To adhere to REST conventions, the version token is mandated as a query parameter (e.g., `DELETE /api/v1/tasks/{id}?version=X`).
* **Conflict Resolution (The UI Contract):** If a mismatch occurs (meaning another user modified or deleted the record in the interim), the database aborts the transaction. 
    * The API returns an `HTTP 409 Conflict` (if modified) or an `HTTP 404 Not Found` (if already deleted). 
    * The frontend explicitly catches these statuses, halts the silent failure, triggers a native browser alert to inform the user of the collision, and automatically forces a background data refresh to reconcile the UI with the latest system state.

**Alternatives Considered:**
* **Pessimistic Locking (`SELECT ... FOR UPDATE`):** Rejected due to the risk of stale locks and poor user experience in long-lived browser sessions.
* **Last-Write-Wins (LWW):** Rejected. Accepting the most recent timestamp without a version check inevitably leads to silent data loss during concurrent edits.
* **Ignoring DELETE Concurrency:** Rejected. Allowing unconditional soft deletes while other users are editing breaks strict state consistency and leads to confusing UI behavior.

**Implementation Path:**
1. Add a `version` integer column (default `1`) to the `todos` SQLAlchemy model.
2. Update all Pydantic schemas for `PUT` and `PATCH` requests to require the `version` field.
3. Update the FastAPI `DELETE` router to mandate `version` as a typed query parameter.
4. Implement targeted error handling in the frontend SPA to intercept `409` and `404` statuses, trigger explicit user alerts, and execute state-reconciliation fetches.

***

This perfectly captures the journey of the feature. Let me know when you are ready to tackle the amendment for **ADR 003 (Task Dependency & State Propagation)**.
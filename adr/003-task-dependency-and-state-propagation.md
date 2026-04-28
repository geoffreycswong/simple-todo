# ADR 003: Task Dependenct and State Propagation

*Status:** Approved (Amended post-MVP iteration)

**Context:**
Tasks can have dependencies, blocking them from being moved to "In Progress" until all prerequisites are completed. The UI requires the ability to instantly filter tasks by their dependency status (blocked vs. unblocked), demanding high-performance read capabilities. During the initial implementation, we mandated strict "Payload Isolation," preventing the frontend from interacting with dependency state. However, user testing revealed that users must be able to add or remove dependencies (`dependency_ids`) on existing tasks via the Edit Modal, requiring a more nuanced boundary between user-declared intentions and system-calculated states.

**Requirements:**
* Fast read access for filtering by `is_blocked` status.
* Strict validation preventing a blocked task from starting.
* Graceful handling of state reversions (reverting a parent task should not retroactively break an already "In Progress" child task).
* Users must be able to modify dependencies post-creation without corrupting the system's boolean lock logic.

**Technical Constraints & Exploration:**
Calculating the blocked status dynamically via SQL subqueries on every `GET` request provides a single source of truth but introduces a massive read penalty at scale. Denormalizing the status into an `is_blocked` boolean column solves the read performance issue but shifts the complexity to the write path.

**Decision (Detailed Architecture):**
We utilized a denormalized `is_blocked` boolean flag alongside an asynchronous background propagation mechanism, but established a strict **Declaration vs. Calculation Boundary**.

* **The Lock Momentum:** The business logic enforces a conditional lock. Prerequisites are only evaluated when transitioning the target state *into* `In Progress`. 
* **The API Boundary:** The frontend is permitted to declare relational intentions by passing an array of `dependency_ids` in `POST` and `PUT` payloads. The frontend is strictly forbidden from passing the `is_blocked` boolean.
* **Dynamic Reassessment:** When the backend receives `dependency_ids` during an update, it validates that the requested dependencies are not soft-deleted. It then links the relationships and dynamically recalculates the `is_blocked` flag on the fly before committing the transaction.
* **Collision Recovery:** When a prerequisite task is marked `Completed`, a background task recalculates downstream `is_blocked` flags, protected by a retry loop to catch OCC `StaleDataError` collisions if a user is simultaneously editing the child task.

**Alternatives Considered:**
* **Dynamic SQL Subqueries:** Rejected due to heavy read penalties during complex filtering.
* **Total Payload Isolation:** Rejected. Preventing the UI from updating `dependency_ids` post-creation degraded the user experience. 

**Implementation Path:**
1. Add `is_blocked` to the database schema.
2. Update the `TodoUpdate` Pydantic schema to accept `dependency_ids`.
3. Implement dynamic recalculation logic inside `crud.update_todo` before the SQLAlchemy commit.
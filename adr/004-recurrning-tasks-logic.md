Here are the final two architectural decision logs to complete the documentation for your SleekFlow project submission. 

# ADR 004: Recurring Tasks Logic

***Status:** Approved

**Context:** The application requires functionality for tasks to recur on varying schedules (daily, weekly, monthly, or custom). The system must automatically generate the next occurrence of a task only when the current instance is marked as "Completed."

**Requirements:**
* Support highly flexible, custom recurrence schedules.
* Prevent database bloat and infinite loops from pre-generating future tasks.
* Handle the ambiguity of recurrence anchors: strictly adhering to the original schedule (e.g., "due on the 1st, regardless of when completed") versus relative scheduling (e.g., "due 7 days after completion").

**Technical Constraints & Exploration:**
Pre-populating a database with future recurring tasks is a common anti-pattern that leads to massive data bloat and complex cascading updates if a user decides to modify or cancel the recurrence rule. Furthermore, custom schedules require a standardized parsing mechanism rather than hardcoded boolean flags (`is_daily`, `is_weekly`).

**Decision (Detailed Architecture):**
We will implement a Procedural Service-Layer Hook triggered upon task completion, utilizing the RFC 5545 iCalendar specification (RRULE).
* **Storage:** The `todos` table will store the recurrence schedule as a standard RRULE string in a `recurrence_rule` column. 
* **Anchor Resolution:** To solve the scheduling ambiguity, a `recurrence_anchor` Enum column (`DUE_DATE` vs. `COMPLETION_DATE`) will dictate the baseline timestamp for the next calculation.
* **The Hook:** When a task's status transitions to `Completed` via the `PATCH` endpoint, the backend calculates the next timestamp using the `dateutil.rrule` library. It then immediately executes an `INSERT` for the new task clone within the same database transaction, ensuring atomicity.

**Alternatives Considered:**
* **Pre-population Engine:** Rejected. Generating 52 rows for a weekly task spanning a year is inefficient and makes updating the schedule logic exceedingly difficult.
* **Asynchronous CRON Sweeper:** Rejected. Running a nightly job to check for completed tasks and generate the next occurrence disconnects the system action from the user action, leading to a confusing UI experience where the next task doesn't appear immediately upon completion.

**Implementation Path:**
1. Add `recurrence_rule` and `recurrence_anchor` columns to the database schema.
2. Integrate the `dateutil` Python library into the FastAPI backend.
3. Implement the procedural hook within the state transition endpoint, ensuring the generation of the next task is covered by a TDD test suite validating both anchor models.


# ADR 006: Real-time Frontend Updates and Synchronization

**Status:** On Hold


**Context:** With multiple users potentially accessing and editing the same TODO list, there is a natural inclination to implement real-time cross-client synchronization so that changes made in one browser tab instantly appear in others. The project prompt notes that this is designed to have more requirements than can be fully implemented, testing prioritization and scoping.

**Requirements:**
* Deliver a robust, fully tested MVP that satisfies all core requirements (CRUD, recurrences, complex dependencies, concurrency handling).
* Sensibly scope the work to focus on core features before "nice-to-haves."
* Maintain a stateless backend architecture that scales horizontally without requiring complex connection management.

**Technical Constraints & Exploration:**
Achieving true real-time synchronization in a distributed, serverless environment (GCP Cloud Run) is architecturally heavy. Because Cloud Run instances scale horizontally and route requests dynamically, holding state in memory is impossible. Implementing WebSockets or Server-Sent Events (SSE) necessitates introducing an infrastructure middleware layer—such as a Redis Pub/Sub instance or GCP Pub/Sub broker—to fan out database update events to all active server containers. Furthermore, long-lived connections (SSE/WebSockets) complicate serverless auto-scaling and scaling to zero, while drastically increasing the complexity of frontend state management.

**Decision (Detailed Architecture):**
We will intentionally defer real-time push synchronization (SSE/WebSockets) to a future phase. The Phase 1 MVP will operate entirely on a pull-based REST architecture. 

To handle the reality of multi-user access without real-time UI updates, we are strictly relying on our Optimistic Concurrency Control (OCC) implementation (Decision 002). If User A is viewing stale data because User B updated a task, User A's subsequent attempt to save will be rejected with an `HTTP 409 Conflict`. The UI will catch this and prompt the user to refresh, ensuring data integrity without the overhead of maintaining persistent streaming connections.

**Alternatives Considered:**
* **WebSockets:** Rejected. WebSockets are bi-directional, which is excessive for an application where the client primarily needs a unidirectional feed of server updates. It also fundamentally breaks the stateless HTTP request-response cycle.
* **Server-Sent Events (SSE) with a Message Broker:** Rejected for Phase 1. While architecturally superior to WebSockets for this use case, introducing a message broker just for UI sugar distracts from delivering the core algorithmic complexity of task dependencies and recurrence hooks. 
* **Short-Polling:** Rejected. Having the frontend ping the `GET /tasks` endpoint every 5 seconds creates unnecessary database load and compute cost on Cloud Run for minimal UX gain.

**Implementation Path (Phase 2 Roadmap):**
1. Provision a lightweight message broker (e.g., GCP Pub/Sub topic: `todo_updates`).
2. Update the backend state-transition logic to publish a lightweight event payload (task ID and new state) to the broker immediately after a successful database commit.
3. Introduce an SSE endpoint (`GET /api/v1/tasks/stream`) in FastAPI.
4. Have active FastAPI worker nodes subscribe to the broker and yield Server-Sent Events down to connected frontend clients to trigger localized UI re-renders.
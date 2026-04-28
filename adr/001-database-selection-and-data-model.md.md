# ADR 001: Database SElection and Data Model

**Status:** Approved

**Context:** The TODO list application requires a robust data foundation capable of handling 10,000+ items per user without performance degradation. The application must support complex filtering and sorting across multiple dimensions, soft deletes, and a self-referencing relationship for task dependencies.

**Requirements:**
* Support for 10,000+ active and soft-deleted items with fast read access.
* Ability to enforce relational integrity for task dependencies.
* Schema flexibility to support future bulk operations or hierarchical task propagation.
* Alignment with a strategic mandate that explicitly excludes core infrastructure maintenance from the development team's scope.

**Technical Constraints & Exploration:**
Evaluating NoSQL document stores against relational SQL databases revealed significant trade-offs. While NoSQL offers flexibility, implementing complex, multi-field sorting combined with relational joins (finding all tasks dependent on Task A) requires heavy application-layer logic and degrades under scale. Furthermore, managing infrastructure like custom database clusters introduces unnecessary operational overhead.

**Decision (Detailed Architecture):**
We will implement a relational database model using PostgreSQL, deployed via the fully managed Google Cloud SQL service. 
* **Identifiers:** `UUID` primary keys will be used instead of sequential integers to prevent enumeration and facilitate distributed generation.
* **Soft Deletes:** A `deleted_at` timestamp column will handle soft deletes. B-Tree indexes will be heavily applied to this column, alongside `status` and `due_date`, to ensure query speeds remain sub-millisecond as the dataset grows.
* **Schema Design:** A primary `todos` table will hold core attributes, while a `task_dependencies` junction table with a composite primary key will manage the many-to-many prerequisite mapping.

**Alternatives Considered:**
* **NoSQL (MongoDB/Firestore):** Rejected. The strict, predictable schema of a TODO item and the heavy reliance on cross-record dependency checking make document stores a poor fit, requiring complex read-side aggregations.
* **Self-hosted PostgreSQL on Compute Engine:** Rejected. Abstracting away OS patching, backups, and disk management via Cloud SQL aligns with maintaining our focus strictly at the platform and service layers.

**Implementation Path:**
1. Provision a PostgreSQL 15 instance via Terraform.
2. Initialize SQLAlchemy ORM in the Python backend.
3. Configure Alembic to manage database migrations, defining the initial tables, UUID generation, and B-Tree indexes.
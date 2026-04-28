
# ADR 011: Strict Obkect Mapping over Payload Spreading

**Status:** Approved

**Context:**
During the final UX refinement, a severe "Payload Pollution" bug was identified. When a user opened a task to edit it, the entire backend object was loaded into the reactive form. If the user closed the modal and clicked "New Task", the form retained backend-only fields (like `status: "Completed"` and `id`). Submitting this polluted payload caused the backend to create brand new tasks that were already marked as completed.

**Requirements:**
* Ensure the frontend payload for task creation is absolutely pristine and matches the exact intent of the user.
* Prevent backend DTO (Data Transfer Object) fields from leaking into frontend mutation requests.
* Provide a clean, deterministic reset state for the form modal.

**Technical Constraints & Exploration:**
The Javascript spread operator (`...newVal`) or `Object.assign()` are frequently used in UI development for rapid data binding. However, when applied to backend responses, they blindly copy immutable or system-managed fields (created_at, updated_at, version, status).

**Decision (Detailed Architecture):**
We mandate **Strict Object Mapping** over dynamic spreading for all reactive form assignments.

* Within the `TaskFormModal.vue` watcher, when a task is selected for editing, the frontend explicitly maps *only* the editable fields (e.g., `form.title = newVal.title || ''`).
* To guarantee payload purity when resetting the form for a "New Task", we explicitly assign default values to every field and execute `delete` statements for known system fields (`delete form.status; delete form.id`).
* This creates a hard architectural barrier between the "Read" schema (what the backend sends) and the "Write" schema (what the frontend form submits).

**Alternatives Considered:**
* **Deep Cloning via `JSON.parse(JSON.stringify())`:** Rejected. While it breaks reference ties, it still copies the polluted fields into the form state.
* **Backend Payload Stripping:** Rejected. Relying exclusively on the backend (Pydantic `exclude_unset` or schema definitions) to ignore bad fields is dangerous. The backend `TodoCreate` schema explicitly allows an optional `status` override for programmatic use, meaning the frontend must be responsible for sending accurate payloads.

**Implementation Path:**
1. Refactor the `watch` block in `TaskFormModal.vue` to remove `Object.assign(form, {...newVal})`.
2. Implement explicit 1-to-1 property mapping for population and defaulting.
3. Add explicit `delete` keywords for `status` and `id` to ensure absolute payload purity on modal close/reset.

***

With these final documents, your project submission tells an incredible story of building, measuring, diagnosing, and architecturally correcting a complex cloud application. You are completely ready for the SleekFlow evaluation!
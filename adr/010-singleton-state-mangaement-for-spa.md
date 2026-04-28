# ADR 010: Singleton State Management for SPA
**Status:** Approved (Supersedes ADR 009)

**Context:**
ADR 009 originally dictated using Vue 3 Composables for "localized reactivity" to avoid the boilerplate of global state stores like Pinia. However, this architectural assumption failed during integration. Because `App.vue` (handling the Create form) and `TaskList.vue` (handling the list display) instantiated entirely separate memory references to the task array, submitting a new task silently updated the background array but left the user-facing list stale until a hard browser refresh.

**Requirements:**
* State mutations triggered in one component (e.g., a modal) must instantly reflect in sibling components (e.g., a list view).
* Centralized tracking of active pagination and filter parameters to ensure data refreshes preserve the user's view.
* Keep bundle size lightweight (avoiding heavy third-party state libraries).

**Technical Constraints & Exploration:**
Passing props and emitting events deeply across a complex component tree (Prop Drilling) creates brittle, tightly coupled UI layers. Introducing Pinia or Vuex solves the synchronization issue but adds unnecessary abstraction layers for a relatively simple CRUD application.

**Decision (Detailed Architecture):**
We implemented a **Global Singleton State Pattern** natively using the Vue 3 Composition API.

* Instead of defining reactive variables (`ref([])`) inside the `export function useTasks()` block, all core state vectors (`tasks`, `currentParams`, `isLoading`) are hoisted *outside* the function scope within the `useTasks.ts` module.
* Because ES modules are evaluated only once, these hoisted variables act as a true global singleton. 
* Any component that imports and executes `useTasks()` now references the exact same memory pointer. When `App.vue` completes a task creation and calls `fetchTasks()`, it updates the shared array, triggering Vue's reactivity engine to instantly re-render `TaskList.vue`.

**Alternatives Considered:**
* **Pinia/Vuex:** Rejected to maintain a minimalist footprint and lower the complexity ceiling.
* **Prop Drilling / Event Bus:** Rejected as it tightly couples components and makes state tracking extremely difficult to debug.

**Implementation Path:**
1. Refactor `useTasks.ts` to hoist `tasks`, `currentParams`, and error states above the exported function.
2. Ensure `fetchTasks` completely overwrites `currentParams.value` rather than merging, to prevent "sticky filters" when users attempt to clear their search criteria.
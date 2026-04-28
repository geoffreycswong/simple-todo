# ADR-009: Frontend State Management and TDD

**Status:** Superseded by ADR 010 (Global Singleton State for SPA Synchronization)

**Context:**
In an earlier iteration, integrating the Vue 3 UI framework led to "Scope Regression"—core functional requirements like filtering and sorting were accidentally dropped because the business logic was too tightly coupled to the Vue components. Additionally, utilizing standard headless browsers (Playwright/Cypress) for Test-Driven Development (TDD) inside the Cloud Shell CLI proved unstable and excessively slow. 

**Update (Post-MVP Friction):** The architectural decision made here to use purely *localized* composable state ultimately failed during integration. Because the reactive state variables (`ref()`) were instantiated *inside* the exported composable function block, sibling components (`App.vue` and `TaskList.vue`) received completely disconnected memory instances. Submitting a new task from the modal updated a hidden state array but left the underlying user-facing list completely stale, requiring manual browser refreshes. This necessitated a pivot to a global singleton pattern (detailed in ADR 010).

**Requirements:**
* Business logic (task lists, filtering, OCC retry logic) must be strictly decoupled from UI rendering.
* The frontend must be developed using a TDD approach that executes flawlessly and rapidly within a terminal environment.
* Prevent the loss of feature requirements when refactoring templates.

**Technical Constraints & Exploration:**
Adding a heavy state management library like Pinia or Vuex introduces boilerplate that is disproportionate to the size of a simple TODO app. Relying on end-to-end (E2E) browser testing for core logic slows down the development loop and frequently fails in restricted cloud IDE environments due to memory or display-server constraints.

**Decision (Historic Architecture):**
*Note: This specific state architecture has been superseded by ADR 010. The TDD strategy remains active.*
We decided to decouple logic using the **Vue 3 Composition API (Composables)** and enforce CLI-based TDD via **Vitest + JSDOM**.
* **Localized State Encapsulation:** All core logic, reactive state (`tasks`, `isLoading`, `error`), and mutation functions were designed to live strictly *inside* a single exported `useTasks()` function, providing isolated reactivity per component.
* **Dumb Components:** The Vue (`.vue`) templates act strictly as a presentation layer.
* **CLI TDD:** By isolating the brain of the app into a pure TypeScript composable, the entire application state can be tested using `vitest` in the terminal, using JSDOM for memory-based reactivity.

**Alternatives Considered:**
* **Pinia / Vuex:** Rejected. Global state store libraries were deemed overkill for a single-view application and increase the learning curve for junior engineers. *(Note: While third-party libraries were rejected, the fundamental need for global state synchronization was ultimately proven necessary and implemented natively in ADR 010).*
* **Playwright / E2E First:** Rejected. While valuable for final integration, E2E testing as the primary TDD driver inside a Cloud Shell environment creates too much friction. Logic tests should run in milliseconds, not seconds.

**Implementation Path (Historic):**
1. Initialize `vitest` and configure the JSDOM environment.
2. Write failing tests for `useTasks.ts` isolated logic.
3. Implement the localized `useTasks.ts` composable.
4. Scaffold the "dumb" Vue components (FilterBar, TaskList) and bind them to the localized composable.
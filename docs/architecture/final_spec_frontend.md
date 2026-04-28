# SimpleTodo Frontend: Final Engineering Specification (As-Built)

## 1. Engineering Philosophy & Architecture
The frontend is a lightweight, functionally robust Single Page Application (SPA). It completely eliminates CORS overhead by utilizing a Single-Container Hybrid Deployment Strategy. 

**Core Stack:** Vue 3 (Composition API), Vite, Tailwind CSS, Vitest (JSDOM).

## 2. Infrastructure & Dev/Prod Parity
* **Local Development:** Vite runs on port `3000`. The `vite.config.ts` utilizes `server.proxy` to intercept `/api` requests and route them to the backend container.
* **Production Deployment:** The frontend is compiled into static assets (`/dist`). The FastAPI backend mounts this directory at `/` and serves `index.html`. The UI and API share the exact same origin in all environments.

## 3. State Management: The Global Singleton Pattern
To ensure absolute UI synchronization without the bloat of third-party state libraries (like Pinia), the application uses a **Global Singleton State Pattern** via Vue Composables (`src/composables/useTasks.ts`).
* Reactive variables (`tasks`, `currentParams`, `isLoading`, `error`) are hoisted **outside** the exported function block.
* This guarantees that when a sibling component (like the Modal) executes a mutation and calls `fetchTasks()`, the underlying state array is updated globally, instantly triggering re-renders in the `TaskList` without requiring browser refreshes.

## 4. The API Integration Layer (Strict Fetch Wrapper)
A dedicated `src/services/api.ts` utility is the sole conduit for backend communication.
* **Stream Safety:** It strictly inspects the `Content-Type` header before parsing to prevent "body stream already read" crashes.
* **Structured Errors:** It intercepts non-OK responses, extracts the FastAPI detail message, and throws a strongly-typed `ApiError` containing the HTTP status code.

## 5. UI Component Architecture

### `FilterBar.vue`
* Manages search criteria: Status, Priority, Dependency State (Blocked/Unblocked), Soft Delete toggle (`is_deleted`), and Sorting (`sort_by`, `order`).
* Emits sanitized payloads (stripping empty strings) to the global `currentParams` object.

### `TaskList.vue` & `TaskItem.vue`
* **Pagination:** Tracks `currentPage` and divides the `X-Total-Count` header by the page size.
* **Due Date UX:** Evaluates the `due_date` against the current date, dynamically applying Tailwind background colors (Red for overdue, Yellow for today, Green for future).
* **Read-Only Mode:** If `task.deleted_at` is populated, the action buttons (Start, Complete, Edit, Delete) are hidden, and the title is styled with a line-through.

### `TaskFormModal.vue`
* Handles both Create and Edit states.
* **Strict Object Mapping:** Implements a strict mapping protocol when initializing the reactive form. It explicitly avoids using `Object.assign()` with backend payloads to prevent "Payload Pollution" (leaking backend-only fields like `status` or `id` into new task creation requests).

### `RRuleGenerator.vue`
* A custom Vue-native component that abstracts the complexity of recurring tasks.
* Provides user-friendly dropdowns (Daily, Weekly, Monthly) and interval inputs, automatically compiling them into valid RFC 5545 RRULE strings for the backend.

## 6. OCC & Error UX Contract
The frontend actively participates in Optimistic Concurrency Control.
* If a mutation (`PUT`, `PATCH`, `DELETE`) throws a `409 Conflict` (version mismatch) or `404 Not Found` (task was deleted by another user), the composable catches the error.
* It fires a native `window.alert()` explaining the conflict to the user.
* It immediately executes `await fetchTasks()` to reconcile the user's screen with the absolute latest state from the database.
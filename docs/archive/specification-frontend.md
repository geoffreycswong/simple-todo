# TODO Application: Frontend Engineering Specification

## 1. Engineering Philosophy & Architecture
This frontend is a lightweight, functionally robust Single Page Application (SPA). It is explicitly designed to eliminate Cross-Origin Resource Sharing (CORS) complexities and ensure a seamless Dev/Prod parity across Google Cloud Shell (local) and GCP Cloud Run (production).

**Core Stack:** Vue 3 (Composition API), Vite, Tailwind CSS, Vitest (for TDD).

### The Hybrid Single-Container Strategy
* **Local Development (Cloud Shell):** The Vite dev server runs on port `3000`. It utilizes `server.proxy` to intercept all `/api/*` requests and tunnel them to the backend Docker container (`http://api:8000`). The browser only communicates with Vite.
* **Production Deployment:** The frontend is compiled into static assets (`npm run build`). The resulting `/dist` folder is copied into the FastAPI backend container. FastAPI mounts this directory at `/` and serves the `index.html`. 
* **Architectural Mandate:** There are no separate frontend and backend URLs in production. The UI and API share the exact same origin.

---

## 2. Environment & Build Configuration

**File:** `vite.config.ts`
To bypass the Cloud Shell CORS proxy issue, implement the following Vite proxy configuration:

```typescript
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://api:8000', // Points to Docker service locally
        changeOrigin: true,
      }
    }
  }
})
```
*Note for Junior Engineer: Never hardcode `http://localhost:8000` here, as `localhost` inside the Vite Docker container refers to the Vite container itself, not the backend container.*

**FastAPI Integration (Backend Update):**
Ensure the backend `main.py` is configured to serve the frontend in production:
```python
from fastapi.staticfiles import StaticFiles
# After defining all /api/v1 routes...
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

---

## 3. The API Integration Layer (Strict Fetch Wrapper)

**File:** `src/services/api.ts`
To prevent the "double-read" stream bug and handle structured REST responses from FastAPI, you must implement a robust API client wrapper.

**Requirements:**
1.  **Single Stream Consumption:** Inspect the `Content-Type` header before parsing. Do not use `try/catch` to guess the response type.
2.  **Structured Errors:** Throw a custom `ApiError` class containing the HTTP status code (vital for identifying 409 OCC and 422 Dependency errors) and the backend error message.

```typescript
// Architectural Blueprint for api.ts
class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/v1${endpoint}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });

  const contentType = response.headers.get('content-type');
  let data;
  
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text(); // Fallback for 204 No Content or raw text errors
  }

  if (!response.ok) {
    // Extract the FastAPI detail message if it exists
    const errorMsg = typeof data === 'object' && data.detail ? data.detail : (data || response.statusText);
    throw new ApiError(response.status, typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
  }
  return data as T;
}
```

---

## 4. State Management (Vue Composables)

**File:** `src/composables/useTasks.ts`
We will bypass heavy state libraries (like Pinia) and use Vue's native Composition API to encapsulate business logic. This ensures logic is testable without a DOM.

**State Vectors:**
* `tasks`: `Ref<Task[]>`
* `isLoading`: `Ref<boolean>`
* `error`: `Ref<string | null>`

**Core Functions:**
1.  `fetchTasks(filters)`: Serializes filter parameters and calls `GET /tasks`.
2.  `updateTaskStatus(id, newStatus, version)`: Calls `PATCH /tasks/{id}/status`. 
    * *Error Handling Rule:* If this throws an `ApiError` with `status === 422` (Blocked) or `409` (OCC Conflict), catch the error, populate the `error` state variable with the user-friendly message, and automatically trigger `fetchTasks()` to refresh the stale data.
3.  `updateTaskDetails(id, payload)`: **Crucial:** The payload must include `version`. The frontend must *strip* the `is_blocked` property from the payload before sending it to the backend, as this is a system-calculated field.

---

## 5. UI Component Architecture

Design is minimal (Tailwind CSS) but functionally complete.

* **`App.vue`**: The main layout wrapper.
* **`FilterBar.vue`**: 
    * Dropdowns for `Status`, `Priority`, and `Dependency Status (Blocked/Unblocked)`.
    * Emits a `@filter-changed` event to the parent to trigger an API re-fetch.
* **`TaskList.vue`**: Renders a list of `TaskItem` components.
* **`TaskItem.vue`**: 
    * Displays Task details, Due Date, and `is_blocked` status visually (e.g., greyed out if blocked).
    * Provides quick-action buttons for status changes. If `is_blocked === true`, the "Start" button must be disabled natively in the DOM.
* **`TaskFormModal.vue`**: 
    * A unified form for Create and Edit.
    * Includes a multi-select field for `dependency_ids` (populating a list of other available tasks to set as prerequisites).

---

## 6. Test-Driven Development (TDD) Guide

All frontend logic must be tested using `vitest` in the Node CLI environment. No headless browser is required for these core logic tests.

**Execution:** Run `npm run test` (mapped to `vitest`) in the Cloud Shell terminal.

**Mandatory Test Suites (Write these before the Vue components):**

1.  **API Wrapper Suite (`api.spec.ts`)**:
    * Mock `global.fetch` to return a `409` status with a JSON payload `{"detail": "Version mismatch"}`.
    * Assert that `apiClient` throws an `ApiError` with `status === 409`.
2.  **State Management Suite (`useTasks.spec.ts`)**:
    * *Test 1 (Fetch):* Mock `apiClient` to return an array of tasks. Call `fetchTasks()` and assert `tasks.value` is populated and `isLoading` toggles correctly.
    * *Test 2 (OCC Recovery):* Mock `apiClient` to throw a 409 error during `updateTaskStatus`. Assert that `error.value` is set to the conflict message, and assert that `fetchTasks()` is automatically called to reconcile the local state.
    * *Test 3 (Dependency Lock):* Attempt to update a task to "In Progress" when it has `is_blocked: true`. (This tests local UI guardrails before even hitting the API).

# ADR 008: API Client and Stream Handling

**Status:** Approved

**Context:**
During frontend prototyping, a critical bug emerged when handling API errors. The application crashed with a `body stream already read` error. This occurred because the code attempted to consume the Fetch API `Response` as JSON, caught the parsing error, and then attempted to consume it again as text. 

**Requirements:**
* The frontend must gracefully handle standard REST responses (200 OK, 204 No Content).
* The frontend must accurately intercept and parse 409 (Optimistic Concurrency Conflict) and 422 (Dependency Violation) errors to drive UI recovery logic.
* The API client must be completely isolated from the UI components.

**Technical Constraints & Exploration:**
The native browser Fetch API dictates that a response body stream can only be consumed once. To read it twice requires using `response.clone()`, which doubles the memory footprint of the payload. Relying on standard `try/catch` blocks around `.json()` across dozens of Vue components leads to code duplication and inconsistent error handling.

**Decision (Detailed Architecture):**
We will implement a **Strict Fetch Wrapper Composable**.
* A dedicated `api.ts` utility will be the sole conduit for backend communication.
* **Stream Inspection:** Before attempting to consume the stream, the wrapper will explicitly inspect the `Content-Type` header. If it includes `application/json`, it will parse via `.json()`; otherwise, it will safely parse via `.text()`.
* **Structured Error Throwing:** If `!response.ok`, the wrapper will extract the specific FastAPI detail message and throw a custom, strongly-typed `ApiError` class containing both the HTTP status code and the message. This allows upstream state managers to easily switch logic based on `error.status === 409`.

**Alternatives Considered:**
* **Axios:** Rejected. While Axios automatically handles JSON parsing and error wrapping, introducing a heavy third-party networking library just to manage stream reading is unnecessary when native Fetch can be wrapped in 30 lines of code. This keeps the bundle size minimal.
* **response.clone():** Rejected. Cloning the network stream for every request just to support a lazy `try/catch` fallback is inefficient and masks the root issue of not checking headers.

**Implementation Path:**
1. Author the `ApiError` class.
2. Build the `apiClient<T>` wrapper with the `Content-Type` inspection logic.
3. Write a Vitest CLI test suite that mocks a 409 JSON error and a 500 Text error to mathematically prove the stream is handled correctly before integrating it with the UI.
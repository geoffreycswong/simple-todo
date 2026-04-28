Here are the frontend-specific architectural decision logs, continuing sequentially from the backend logs.

# ADR 007: Frontend Deplotment and CORS Strategy

**Status:** Approved

**Context:** The application needs to be developed and tested in a Google Cloud Shell (Cloud IDE) environment before being deployed to GCP Cloud Run. Previous iterations encountered severe network routing issues, as Cloud Shell proxies ports (e.g., 3000 and 8000) to dynamic hostnames wrapped in an authentication layer. This caused cross-origin (CORS) `fetch` requests to fail with silent `302` redirects, halting development.

**Requirements:**
* Establish a frictionless local development loop inside Cloud Shell.
* Completely eliminate CORS complexities and preflight (`OPTIONS`) request overhead.
* Achieve strict Dev/Prod parity to ensure the deployed application behaves identically to the local environment.
* Keep the infrastructure footprint minimal (stateless, managed services).

**Technical Constraints & Exploration:**
Attempting to wildcard CORS headers (`Access-Control-Allow-Origin: *`) in the backend API does not bypass the Cloud Shell IDE's security proxy. Running two separate Cloud Run services in production (one for the SPA frontend, one for the API) introduces unnecessary domain routing complexity, requires managing multiple CI/CD pipelines, and re-introduces cross-origin network latency. 

**Decision (Detailed Architecture):**
We will implement a **Single-Container Hybrid Deployment Strategy**.
* **Local Architecture:** The frontend will use Vite's internal development server (`localhost:3000`). We will configure Vite's `server.proxy` to intercept all requests starting with `/api` and route them internally to the backend Docker container. As a result, the browser only ever communicates with a single origin.
* **Production Architecture:** We will use a multi-stage Docker build. The frontend will be compiled into static HTML/JS/CSS assets (`npm run build`). The FastAPI backend will be configured to mount these static files at the root route (`/`). 
* **Result:** The UI and the API share the exact same origin in both environments, completely bypassing CORS constraints.

**Alternatives Considered:**
* **Separate Cloud Run Services:** Rejected. Deploying the frontend on Firebase Hosting or a separate Cloud Run instance increases infrastructure overhead and forces us to manage CORS headers for production, which violates the goal of architectural simplicity.
* **Disabling Cloud Shell Web Preview Security:** Rejected. Attempting to bypass the IDE's security mechanisms is a brittle workaround that does not translate to a stable production configuration.

**Implementation Path:**
1. Configure `vite.config.ts` with a proxy routing `/api` to the backend container (using the Docker service name, not `localhost`).
2. Update the backend `main.py` using `FastAPI.staticfiles` to mount the `/dist` directory in production.
3. Remove all CORS middleware from the FastAPI application, as it is no longer required.
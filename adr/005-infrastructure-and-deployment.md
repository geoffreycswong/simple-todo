# ADR 005: Infrastructure and Deployment


**Status:** Approved

**Context:**
The application must be reproducibly built and deployed on the cloud, while maintaining a local version that is extremely easy to run and test. The operational mandate for the backend requires staying strictly at the platform and service layers, eliminating any need for core infrastructure maintenance.

**Requirements:**
* Strict Dev/Prod parity to ensure local tests guarantee cloud stability.
* Frictionless local setup for TDD execution.
* Automated, reproducible cloud provisioning.
* Zero maintenance of underlying operating systems, VMs, or complex networking infrastructure.

**Technical Constraints & Exploration:**
Managing traditional container orchestration engines like Kubernetes introduces significant administrative overhead that distracts from feature delivery. However, deploying raw code without containerization violates Dev/Prod parity and leads to configuration drift. A bridge is required to execute the exact same application artifact locally and in the cloud.

**Decision (Detailed Architecture):**
We will adopt a Dual-Deployment Strategy utilizing 12-Factor App principles, connected exclusively via environment variables.
* **The Bridge:** Application configuration will be managed via `pydantic-settings`, relying on `APP_ENV` and `DATABASE_URL` to route connections without hardcoded logic.
* **Local Development:** A `docker-compose.yml` file will provision a local PostgreSQL instance alongside the FastAPI application container. The code directory will be bind-mounted into the container to enable hot-reloading for rapid TDD cycles.
* **Cloud Production:** We will use Terraform to provision a fully serverless stack on GCP. 
    * Google Cloud SQL will provide a fully managed PostgreSQL database.
    * Google Cloud Run will host the stateless FastAPI container, scaling automatically with concurrent web traffic and scaling to zero when idle.
* **Database Migrations:** The Docker container entrypoint will be configured to execute `alembic upgrade head` before starting the web server, ensuring database schemas are automatically synced upon deployment in both environments.

**Alternatives Considered:**
* **Google Kubernetes Engine (GKE):** Rejected. While highly scalable, managing nodes, ingress controllers, and pod networking falls into core infrastructure maintenance, which explicitly violates our operational boundaries for this project.
* **Local Python Virtual Environment (venv) without Docker:** Rejected for the primary local setup. While faster to boot initially, it requires the developer to manually install and manage a local Postgres server, breaking Dev/Prod parity and increasing onboarding friction.

**Implementation Path:**
1. Author the `docker-compose.yml` and `Dockerfile` optimized for local development and hot-reloading.
2. Write Terraform configurations (`main.tf`, `variables.tf`) to define the Cloud SQL, Artifact Registry, and Cloud Run resources.
3. Configure the Alembic migration execution within the container startup sequence.

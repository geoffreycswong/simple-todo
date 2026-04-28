# SimpleTodo Deployment Plan: Google Cloud Platform (GCP)

This plan outlines the steps to deploy the SimpleTodo application using a **Single-Container Hybrid Deployment Strategy** on Cloud Run, with Cloud SQL for PostgreSQL as the database.

## 1. Prerequisites & Environment Setup

### Tools Required
- [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install)
- Docker (for local testing, optional)

### Environment Variables
Set these variables in your terminal for easier execution:
```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export DB_INSTANCE_NAME="todo-db-instance"
export DB_NAME="todo_db"
export DB_USER="todo_user"
export DB_PASS="your-secure-password" # Use a secure generator
export SERVICE_NAME="simpletodo-app"
export REPO_NAME="simpletodo-repo"
```

---

## 2. GCP Project Initialization

### Create Project & Set Context
```bash
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID
```

### Enable Necessary APIs
```bash
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com
```

---

## 3. Infrastructure Setup (Cloud SQL)

### Create Cloud SQL Instance
```bash
gcloud sql instances create $DB_INSTANCE_NAME \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=$DB_PASS
```

### Create Database & User
```bash
gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE_NAME
gcloud sql users create $DB_USER --instance=$DB_INSTANCE_NAME --password=$DB_PASS
```

---

## 4. Secret Management

Store the database connection string in Secret Manager to avoid plain-text environment variables.

### Define the Connection String
The format for Cloud Run to Cloud SQL (via Unix Socket) is:
`postgresql://USER:PASSWORD@/DB_NAME?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_ID`

```bash
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe $DB_INSTANCE_NAME --format='value(connectionName)')
DATABASE_URL="postgresql://$DB_USER:$DB_PASS@/$DB_NAME?host=/cloudsql/$INSTANCE_CONNECTION_NAME"

echo -n $DATABASE_URL | gcloud secrets create DATABASE_URL --data-file=-
```

### Grant Access to Cloud Run
The Cloud Run service account needs access to the secret and the SQL instance.
```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
RUN_SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# Grant Secret Access
gcloud secrets add-iam-policy-binding DATABASE_URL \
    --member="serviceAccount:$RUN_SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Grant SQL Client Access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$RUN_SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client"
```

---

## 5. Build & Containerization

### Create Artifact Registry
```bash
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for SimpleTodo"
```

### Build and Push Image
Using Cloud Build allows for remote building without local Docker overhead.
```bash
IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:latest"
gcloud builds submit --tag $IMAGE_TAG .
```

---

## 6. Deployment to Cloud Run

### Initial Deployment
```bash
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_TAG \
    --region $REGION \
    --set-secrets "DATABASE_URL=DATABASE_URL:latest" \
    --add-cloudsql-instances $INSTANCE_CONNECTION_NAME \
    --set-env-vars "APP_ENV=production" \
    --allow-unauthenticated
```

---

## 7. Database Migrations

Run Alembic migrations against the production database. You can do this from your local machine (using Cloud SQL Auth Proxy) or via a temporary Cloud Build job.

### Option: Run via Cloud Build (Recommended for CI/CD)
Create a `migration.yaml`:
```yaml
steps:
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: 'bash'
  args:
    - '-c'
    - 'pip install -r backend/requirements.txt && alembic upgrade head'
  env:
    - 'DATABASE_URL=$_DATABASE_URL'
```

Execute:
```bash
gcloud builds submit --config migration.yaml --substitutions _DATABASE_URL=$DATABASE_URL .
```

---

## 8. Verification

1. **Check Status:**
   ```bash
   gcloud run services describe $SERVICE_NAME --region $REGION
   ```
2. **Access URL:** The command output will provide a Service URL (e.g., `https://simpletodo-app-xyz.a.run.app`).
3. **Smoke Test:**
   - Open the URL in a browser to see the Vue frontend.
   - Create a task to verify backend-to-DB connectivity.
   - Refresh to ensure data persists.

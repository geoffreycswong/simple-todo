# Stage 1: Build Frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Backend
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
# Copy frontend assets from build stage
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
ENV PYTHONPATH=/app
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}

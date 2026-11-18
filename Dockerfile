# ==============================================================================
# MarketPath AI — Multi-Stage Production Dockerfile (Single-Service Deployment)
# Stage 1: Build React/Vite Frontend
# Stage 2: Python 3.12-Slim FastAPI Backend serving API + SPA Static Files
# ==============================================================================

# Stage 1: Build Frontend Assets
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime Backend & Static Serving
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8000

# Install runtime system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./backend/

# Copy built frontend assets from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create unprivileged user for security
RUN addgroup --system --gid 1001 marketpath && \
    adduser --system --uid 1001 --ingroup marketpath marketpath && \
    mkdir -p /app/secrets && \
    chown -R marketpath:marketpath /app

USER marketpath

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Execute startup with database seeding verification and dynamic port listener
CMD ["sh", "-c", "python -m backend.scripts.seed_demo && uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

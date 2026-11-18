#!/bin/sh
set -e

echo "=================================================================="
echo "MarketPath AI — Production Container Startup Lifecycle"
echo "=================================================================="

# 1. Validate required environment variables and encryption keys
echo "[1/5] Validating environment configuration and cryptographic master keys..."
python -c "
from backend.app.core.config import settings
print(f'Configuration valid. Environment: {settings.APP_ENV}, Port: {settings.PORT}')
"

# 2. Execute Alembic database migrations
echo "[2/5] Executing database schema migrations (Alembic)..."
python -m alembic -c backend/alembic.ini upgrade head

# 3. Provision demo accounts & default fixtures safely
echo "[3/5] Provisioning canonical recruiter demo accounts..."
python -m backend.scripts.seed_demo

# 4. Validate dataset invariants
echo "[4/5] Running automated demo invariant verification suite..."
python -m backend.scripts.verify_demo_data

# 5. Start dynamic port listener
echo "[5/5] Launching Uvicorn ASGI server on port ${PORT:-8000}..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

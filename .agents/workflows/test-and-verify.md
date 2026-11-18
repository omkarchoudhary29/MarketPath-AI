# Workflow: Perform Full Feature Testing & Verification

Use this workflow to perform full regression verification before committing changes or declaring a feature complete.

## Step 1: Backend Automated Pytest Suite
Run the full 55-test suite covering all 9 core modules and MarketPath Agency Connect:
```bash
python -m pytest backend/tests -v
```
- **Acceptance Criterion:** 55 passed, 0 failures, 0 errors.

## Step 2: Database Schema & Migration Verification
Verify Alembic migration state:
```bash
alembic -c backend/alembic.ini current
```
- **Acceptance Criterion:** Current head matches latest migration script.

## Step 3: Frontend Type Check & Production Bundle
Verify TypeScript types and Vite production build:
```bash
npm --prefix frontend run build
```
- **Acceptance Criterion:** Exit code 0, 0 TypeScript errors, bundle generated in `frontend/dist/`.

## Step 4: Health Check & Security Header Verification
Verify live backend health and headers:
```bash
python -c "import urllib.request; resp = urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health'); print(resp.status, dict(resp.headers))"
```
- **Acceptance Criterion:** HTTP 200, `database: connected`, security headers present (`nosniff`, `DENY`, `X-Request-Id`).


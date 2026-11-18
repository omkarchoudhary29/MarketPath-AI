# Workflow: Implement a New MarketPath Feature

Use this workflow when designing and implementing a new vertical feature slice in MarketPath AI.

## Step 1: Requirements & Architecture Alignment
1. Consult `README.md` for project context, requirements, and system architecture.
2. Check existing models in `backend/app/models/` and schemas in `backend/app/schemas/` to avoid duplication.
3. Design API contracts adhering to `README.md` specifications:
   - JSON envelope: `{ "data": ..., "meta": ... }` or `{ "error": { "code": ..., "message": ... } }`.
   - Explicit HTTP status codes (`200 OK`, `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `429 Too Many Requests`).

## Step 2: Database Model & Alembic Migration
1. Define declarative SQLAlchemy 2.0 model with `organization_id` foreign key.
2. Generate and verify Alembic migration script in `backend/alembic/versions/`.
3. Apply migration: `alembic -c backend/alembic.ini upgrade head`.

## Step 3: Backend Service & Endpoints
1. Implement business logic in `backend/app/services/<feature>_service.py`.
2. Create router endpoints in `backend/app/api/v1/endpoints/<feature>.py`.
3. Protect routes with `get_current_tenant_context` and role-based permissions (`require_role(...)`).
4. Register router in `backend/app/api/v1/router.py`.

## Step 4: Frontend Component & State
1. Define TypeScript interfaces matching backend Pydantic schemas in `frontend/src/types/`.
2. Connect to API using `apiClient` with automatic `X-Organization-Id` injection.
3. Add accessible UI components in `frontend/src/components/` and routes in `frontend/src/routes/AppRoutes.tsx`.
4. Ensure responsive layouts (mobile, tablet, desktop) and empty/loading states.

## Step 5: Verification & Testing
1. Write backend pytest test suite in `backend/tests/test_<feature>.py` covering:
   - Happy path CRUD.
   - Validation failures (HTTP 422).
   - Cross-tenant access denial (HTTP 404 or 403).
2. Run tests: `python -m pytest backend/tests/test_<feature>.py -v`.
3. Verify production build: `npm --prefix frontend run build`.


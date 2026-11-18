---
name: review-backend-api
description: Review, profile, and debug FastAPI backend endpoints for tenant isolation, RBAC checks, Pydantic schemas, and query performance.
---

# Review and Debug a Backend API

Use this skill to review, profile, or debug FastAPI backend endpoints.

## Step 1: Health & Diagnostics
1. Check backend liveness and readiness:
   - `GET /health` -> `{"status": "healthy"}`
   - `GET /api/v1/health` -> `{"database": "connected"}`
2. Check FastAPI startup logs for uncaught initialization exceptions.

## Step 2: Route Security & Isolation Audit
1. Inspect endpoint dependencies in `backend/app/api/v1/endpoints/`:
   - Is `get_current_tenant_context` injected?
   - Is `require_role(UserRole.ADMIN, ...)` or appropriate RBAC dependency present for mutating endpoints?
   - Is `X-Organization-Id` strictly scoped in database `where(...)` clauses?
2. Verify that sensitive fields (e.g. `cost_price`) are sanitized before serialization to non-owner roles.

## Step 3: Schema & Payload Validation
1. Verify Pydantic v2 schemas:
   - Does model use `ConfigDict(from_attributes=True)`?
   - Are optional fields typed as `Optional[T] = None`?
   - Does response envelope match `{ "data": ... }` standard?

## Step 4: Database Query Performance
1. Inspect SQLAlchemy queries for `N+1` query antipatterns.
2. Use `selectinload` or `joinedload` on relationships (`variants`, `media`, `services`).
3. Ensure database indexes exist for queried columns (`organization_id`, `sku`, `status`).

## Step 5: Test Execution & Verification
1. Run targeted pytest suite:
   ```bash
   python -m pytest backend/tests/test_<module>.py -v
   ```
2. Verify rate limiting behavior and security response headers (`X-Content-Type-Options: nosniff`, `X-Request-Id`).


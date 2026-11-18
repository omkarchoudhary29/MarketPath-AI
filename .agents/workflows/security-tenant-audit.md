# Workflow: Security & Tenant Isolation Audit

Use this workflow to audit tenant boundaries, RBAC permissions, and token security across MarketPath AI.

## Step 1: Adversarial Tenant Boundary Verification
1. Run multi-tenancy pytest test suite:
   ```bash
   python -m pytest backend/tests/test_tenancy.py -v
   ```
2. Verify that:
   - Request lacking `X-Organization-Id` returns HTTP 400.
   - Request with valid JWT for Org A attempting to access Org B resource returns HTTP 404 or 403.
   - Cross-tenant mutations (update, delete) are strictly rejected.

## Step 2: Role-Based Access Control (RBAC) Audit
1. Run RBAC test suite:
   ```bash
   python -m pytest backend/tests/test_rbac.py backend/tests/test_admin.py -v
   ```
2. Verify:
   - `Viewer` role cannot create products, initiate publishing, or approve campaigns.
   - `cost_price` is omitted from serialized product responses for non-admin roles.
   - Regular sellers cannot access `/api/v1/admin/*` endpoints.

## Step 3: Token Encryption & Secret Audit
1. Run encryption tests:
   ```bash
   python -m pytest backend/tests/test_auth.py -k "test_token_encryption_at_rest" -v
   ```
2. Check database tables directly to confirm `channel_connections.encrypted_access_token` contains base64-encoded ciphertext and authentication tag rather than plaintext tokens.
3. Verify `.env` is absent from Git tracking: `git status --ignored`.

## Step 4: Rate Limiting & Webhook Cryptography
1. Run webhook signature tests:
   ```bash
   python -m pytest backend/tests/test_webhooks.py -v
   ```
2. Verify that invalid HMAC signatures return HTTP 401 Unauthorized.
3. Test sliding-window rate limiter under rapid request load.


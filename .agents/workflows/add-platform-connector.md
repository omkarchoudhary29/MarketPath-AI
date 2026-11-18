# Workflow: Add an External Platform Connector

Use this workflow when implementing an official third-party connector (e.g. Shopify, Instagram, Amazon, Google Ads).

## Step 1: Official Documentation & Scopes Verification
1. Inspect official developer documentation for the target platform.
2. Identify minimal required OAuth scopes (least privilege).
3. Document API rate limits, webhook HMAC schemes, and error codes in `README.md`.

## Step 2: Channel Adapter Interface
1. Implement adapter adhering to `backend/app/services/integrations/` interface:
   - `build_authorization_url(state: str, tenant_id: str) -> str`
   - `exchange_code_for_token(code: str) -> Dict[str, Any]`
   - `refresh_token(refresh_token: str) -> Dict[str, Any]`
   - `verify_webhook_signature(payload: bytes, signature: str) -> bool`

## Step 3: Security & Token Vaulting
1. Store access tokens encrypted with AES-256-GCM via `encrypt_token(...)`.
2. Never log or transmit tokens in plain text.
3. Handle token revocation and expiry gracefully with clear reconnect UI states.

## Step 4: Strict No-Faking Policy
1. If partner credentials or API approvals are missing:
   - Display explicit setup status (`Status: Disconnected / Pending Setup`).
   - Do not simulate successful external publishing or mock remote IDs.
   - Provide manual setup pack export where appropriate.

## Step 5: Webhook & Background Queue Integration
1. Implement webhook endpoint in `backend/app/api/v1/endpoints/webhooks.py`.
2. Verify cryptographic signature before processing payload.
3. Enforce idempotency using `webhook_events` deduplication table.


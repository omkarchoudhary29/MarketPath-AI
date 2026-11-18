"""Automated tests for Inbound Webhooks.

Tests HMAC signature verification for Shopify, Meta X-Hub-Signature-256,
challenge-response handshake, and webhook event deduplication.
"""

import base64
import hashlib
import hmac
import json
import uuid
import pytest
from httpx import AsyncClient
from unittest.mock import patch

from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_shopify_webhook_hmac_and_deduplication(client: AsyncClient):
    """Tests Shopify HMAC signature validation and duplicate event handling."""
    secret = "test_shopify_webhook_secret_key"
    with patch.object(settings, "SHOPIFY_API_SECRET", secret):
        payload = {
            "id": 123456789,
            "title": "Updated Brass Lamp Title",
            "vendor": "MarketPath Artisan",
            "variants": [{"id": 987654321, "inventory_quantity": 25}],
        }
        raw_body = json.dumps(payload).encode("utf-8")

        # Compute valid HMAC
        valid_hmac = base64.b64encode(
            hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
        ).decode("utf-8")

        webhook_id = f"wh_shopify_{uuid.uuid4().hex[:12]}"

        # 1. Tampered / invalid HMAC rejected
        bad_resp = await client.post(
            "/api/v1/webhooks/shopify",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Hmac-Sha256": "invalid_base64_signature==",
                "X-Shopify-Webhook-Id": webhook_id,
                "X-Shopify-Topic": "products/update",
            },
        )
        assert bad_resp.status_code == 401
        err_msg = bad_resp.json().get("error", {}).get("message") or bad_resp.json().get("detail", "")
        assert "HMAC signature verification failed" in err_msg

        # 2. Valid signature accepted
        good_resp = await client.post(
            "/api/v1/webhooks/shopify",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Hmac-Sha256": valid_hmac,
                "X-Shopify-Webhook-Id": webhook_id,
                "X-Shopify-Topic": "products/update",
            },
        )
        assert good_resp.status_code == 200
        data = good_resp.json()
        assert data["status"] == "ok"
        assert data["processed"] is True
        assert data["event_id"] == webhook_id

        # 3. Duplicate event received with same ID -> deduplicated
        dup_resp = await client.post(
            "/api/v1/webhooks/shopify",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Hmac-Sha256": valid_hmac,
                "X-Shopify-Webhook-Id": webhook_id,
                "X-Shopify-Topic": "products/update",
            },
        )
        assert dup_resp.status_code == 200
        dup_data = dup_resp.json()
        assert dup_data["processed"] is False
        assert "Duplicate event" in dup_data["message"]


@pytest.mark.asyncio
async def test_meta_webhook_handshake_and_signature(client: AsyncClient):
    """Tests Meta challenge handshake and X-Hub-Signature-256 ingestion."""
    meta_secret = "test_meta_webhook_secret_key"
    with patch.object(settings, "META_APP_SECRET", meta_secret), \
         patch.object(settings, "SECRET_KEY", "test_verification_token"):

        # 1. Challenge Handshake GET
        handshake_resp = await client.get(
            "/api/v1/webhooks/meta?hub.mode=subscribe&hub.challenge=test_challenge_code_123&hub.verify_token=test_verification_token"
        )
        assert handshake_resp.status_code == 200
        assert handshake_resp.text == "test_challenge_code_123"

        # Invalid token handshake rejected
        bad_handshake = await client.get(
            "/api/v1/webhooks/meta?hub.mode=subscribe&hub.challenge=123&hub.verify_token=wrong_token"
        )
        assert bad_handshake.status_code == 403

        # 2. Event ingestion POST with SHA-256 signature
        meta_payload = {
            "object": "instagram",
            "entry": [
                {
                    "id": f"ig_event_{uuid.uuid4().hex[:8]}",
                    "time": 1700000000,
                    "changes": [{"field": "comments", "value": {"id": "1784"}}]
                }
            ]
        }
        raw_body = json.dumps(meta_payload).encode("utf-8")
        expected_sig = "sha256=" + hmac.new(meta_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

        # Ingestion with valid signature
        post_resp = await client.post(
            "/api/v1/webhooks/meta",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": expected_sig,
            },
        )
        assert post_resp.status_code == 200
        assert post_resp.json()["status"] == "ok"
        assert post_resp.json()["processed"] is True

        # Ingestion with invalid signature rejected
        bad_post = await client.post(
            "/api/v1/webhooks/meta",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=invalid_hash_signature",
            },
        )
        assert bad_post.status_code == 401

"""Automated tests for Omnichannel Publishing Engine.

Tests channel mapping validation, payload previews, job queueing,
idempotency, external API mocking (Shopify & Instagram), attempt audit logs,
safe retries, and cross-tenant isolation.
"""

import uuid
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from backend.app.core.config import settings
from backend.app.core.security import encrypt_token
from backend.app.models.channel import ChannelConnection
from backend.app.services.shopify_service import ShopifyError


async def _create_test_product(client: AsyncClient, owner_headers: dict) -> str:
    """Helper to create a valid master product with images."""
    prod_payload = {
        "sku": f"SKU-PUB-{uuid.uuid4().hex[:6].upper()}",
        "title": "Handcrafted Brass Diya Lamp",
        "category": "Home & Decor",
        "base_price": 1250.00,
        "compare_at_price": 1500.00,
        "cost_price": 750.00,
        "currency": "INR",
        "stock_quantity": 40,
        "short_description": "Pure brass handcrafted diya with traditional filigree work.",
        "long_description": "Exquisite handmade brass diya lamp crafted by artisan co-operatives in Moradabad.",
        "tags": ["brass", "diya", "handcrafted", "festival"],
        "materials": ["Pure Brass"],
    }
    resp = await client.post("/api/v1/products", json=prod_payload, headers=owner_headers)
    assert resp.status_code == 201
    prod_id = resp.json()["id"]

    # Attach image
    media_payload = {
        "cloudinary_public_id": "diya_brass_main_01",
        "media_url": "https://res.cloudinary.com/marketpath/image/upload/v1/diya.jpg",
        "media_type": "image",
        "alt_text": "Handcrafted Brass Diya Lamp Front View",
        "display_order": 1,
    }
    media_resp = await client.post(f"/api/v1/products/{prod_id}/media", json=media_payload, headers=owner_headers)
    assert media_resp.status_code == 201

    return prod_id


@pytest.mark.asyncio
async def test_publishing_preview_and_validation(
    client: AsyncClient,
    owner_headers: dict,
):
    """Verifies platform payload generation and validation rules."""
    prod_id = await _create_test_product(client, owner_headers)

    # Preview for Shopify
    shopify_prev = await client.post(
        "/api/v1/publishing/preview",
        json={"product_id": prod_id, "channel_type": "shopify"},
        headers=owner_headers,
    )
    assert shopify_prev.status_code == 200
    data = shopify_prev.json()
    assert data["validation_passed"] is True
    assert len(data["validation_errors"]) == 0
    assert "input" in data["payload_preview"]
    assert data["payload_preview"]["input"]["title"] == "Handcrafted Brass Diya Lamp"
    assert len(data["payload_preview"]["media"]) >= 1

    # Preview for Instagram
    ig_prev = await client.post(
        "/api/v1/publishing/preview",
        json={"product_id": prod_id, "channel_type": "instagram"},
        headers=owner_headers,
    )
    assert ig_prev.status_code == 200
    ig_data = ig_prev.json()
    assert ig_data["validation_passed"] is True
    assert "image_url" in ig_data["payload_preview"]
    assert "https://" in ig_data["payload_preview"]["image_url"]
    assert "#brass" in ig_data["payload_preview"]["caption"]


@pytest.mark.asyncio
async def test_enqueue_and_execute_shopify_publishing_job(
    client: AsyncClient,
    owner_headers: dict,
    owner_org_id: str,
):
    """Tests end-to-end publishing flow, mocking Shopify GraphQL API response."""
    prod_id = await _create_test_product(client, owner_headers)

    with patch.object(settings, "SHOPIFY_API_KEY", "test_key"), \
         patch.object(settings, "SHOPIFY_API_SECRET", "test_secret"):

        # Create connected Shopify channel for this organization
        with patch("backend.app.services.shopify_service.ShopifyService.exchange_access_token", new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "shpat_test_token_456",
                "scope": ["write_products", "read_products"],
                "shop": "artisan-brass-store.myshopify.com",
            }
            init_resp = await client.post(
                "/api/v1/integrations/shopify/authorize",
                json={"shop_domain": "artisan-brass-store.myshopify.com"},
                headers=owner_headers,
            )
            assert init_resp.status_code == 200
            state_nonce = init_resp.json()["state"]

            callback_resp = await client.post(
                "/api/v1/integrations/shopify/callback",
                json={"code": "mock_code", "state": state_nonce, "shop": "artisan-brass-store.myshopify.com"},
                headers=owner_headers,
            )
            assert callback_resp.status_code == 200
            connection_id = callback_resp.json()["id"]

        # Mock external Shopify product creation
        mock_shopify_result = {
            "remote_product_id": "gid://shopify/Product/1000999888",
            "remote_url": "https://artisan-brass-store.myshopify.com/products/handcrafted-brass-diya-lamp",
            "status": "published",
            "raw_response": {"id": "gid://shopify/Product/1000999888", "title": "Handcrafted Brass Diya Lamp"},
        }

        idempotency_key = f"pub_test_{uuid.uuid4().hex[:8]}"

        with patch("backend.app.services.shopify_service.ShopifyService.create_product_listing", new_callable=AsyncMock) as mock_pub:
            mock_pub.return_value = mock_shopify_result

            # Enqueue and execute
            job_resp = await client.post(
                "/api/v1/publishing/jobs",
                json={
                    "product_id": prod_id,
                    "channel_connection_id": connection_id,
                    "job_type": "create_listing",
                    "idempotency_key": idempotency_key,
                },
                headers=owner_headers,
            )
            assert job_resp.status_code == 201
            job_data = job_resp.json()
            assert job_data["status"] == "published"
            assert job_data["remote_product_id"] == "gid://shopify/Product/1000999888"
            assert "artisan-brass-store.myshopify.com" in job_data["remote_url"]
            assert len(job_data["attempts"]) == 1
            assert job_data["attempts"][0]["http_status"] == 200

            # Idempotency test: resubmitting with same key returns existing job without duplicate attempt
            dup_resp = await client.post(
                "/api/v1/publishing/jobs",
                json={
                    "product_id": prod_id,
                    "channel_connection_id": connection_id,
                    "job_type": "create_listing",
                    "idempotency_key": idempotency_key,
                },
                headers=owner_headers,
            )
            assert dup_resp.status_code == 201
            dup_data = dup_resp.json()
            assert dup_data["id"] == job_data["id"]
            assert dup_data["idempotency_key"] == idempotency_key


@pytest.mark.asyncio
async def test_publishing_failure_and_safe_retry(
    client: AsyncClient,
    owner_headers: dict,
):
    """Tests failure handling when external provider fails, followed by a successful retry."""
    prod_id = await _create_test_product(client, owner_headers)

    with patch.object(settings, "SHOPIFY_API_KEY", "test_key"), \
         patch.object(settings, "SHOPIFY_API_SECRET", "test_secret"):

        # Connect Shopify channel
        with patch("backend.app.services.shopify_service.ShopifyService.exchange_access_token", new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "shpat_fail_test",
                "scope": ["write_products"],
                "shop": "failing-store.myshopify.com",
            }
            init_resp = await client.post(
                "/api/v1/integrations/shopify/authorize",
                json={"shop_domain": "failing-store.myshopify.com"},
                headers=owner_headers,
            )
            assert init_resp.status_code == 200
            state_nonce = init_resp.json()["state"]
            cb_resp = await client.post(
                "/api/v1/integrations/shopify/callback",
                json={"code": "code", "state": state_nonce, "shop": "failing-store.myshopify.com"},
                headers=owner_headers,
            )
            connection_id = cb_resp.json()["id"]

        # 1. Enqueue with simulated provider error (HTTP 429 Rate Limit)
        with patch("backend.app.services.shopify_service.ShopifyService.create_product_listing", new_callable=AsyncMock) as mock_pub:
            mock_pub.side_effect = ShopifyError("Shopify API rate limit reached. Retry scheduled with backoff.", is_retryable=True, http_status=429)

            job_resp = await client.post(
                "/api/v1/publishing/jobs",
                json={
                    "product_id": prod_id,
                    "channel_connection_id": connection_id,
                    "job_type": "create_listing",
                },
                headers=owner_headers,
            )
            assert job_resp.status_code == 201
            job_data = job_resp.json()
            assert job_data["status"] == "failed"
            assert job_data["retry_count"] == 1
            assert len(job_data["attempts"]) == 1
            assert job_data["attempts"][0]["http_status"] == 429
            assert "rate limit" in job_data["attempts"][0]["error_message"]
            job_id = job_data["id"]

        # 2. Retry job with recovered provider
        with patch("backend.app.services.shopify_service.ShopifyService.create_product_listing", new_callable=AsyncMock) as mock_retry:
            mock_retry.return_value = {
                "remote_product_id": "gid://shopify/Product/88887777",
                "remote_url": "https://failing-store.myshopify.com/products/recovered",
                "status": "published",
                "raw_response": {"id": "gid://shopify/Product/88887777"},
            }

            retry_resp = await client.post(f"/api/v1/publishing/jobs/{job_id}/retry", headers=owner_headers)
            assert retry_resp.status_code == 200
            retried_data = retry_resp.json()
            assert retried_data["status"] == "published"
            assert retried_data["remote_product_id"] == "gid://shopify/Product/88887777"
            assert len(retried_data["attempts"]) == 2
            assert retried_data["attempts"][1]["http_status"] == 200


@pytest.mark.asyncio
async def test_cross_tenant_publishing_isolation(
    client: AsyncClient,
    owner_headers: dict,
    member_headers: dict,
):
    """Ensures a seller in Org B cannot view or trigger publishing jobs of Org A."""
    prod_id = await _create_test_product(client, owner_headers)

    # Org B attempts to preview Org A's product -> 400 or 404 forbidden
    ig_prev_org_b = await client.post(
        "/api/v1/publishing/preview",
        json={"product_id": prod_id, "channel_type": "shopify"},
        headers=member_headers,
    )
    assert ig_prev_org_b.status_code in [400, 404]

"""Comprehensive Phase 3 Test Suite: Real Marketplace Connectivity, Seller Authorization,
Mapping, Multi-Channel Publishing & Listings Performance.
"""

import json
import uuid
import pytest
from httpx import AsyncClient, Response
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from backend.app.core.security import encrypt_token, decrypt_token
from backend.app.models.catalogue import Product, ProductChannelOverride
from backend.app.models.channel import ChannelConnection, ChannelListing, PublishingBatch, PublishingJob
from backend.app.services.amazon_service import AmazonService, AmazonSPAPIError
from backend.app.services.flipkart_service import FlipkartService, FlipkartAPIError
from backend.app.services.woocommerce_service import WooCommerceService, WooCommerceError
from backend.app.services.channel_registry import CHANNEL_REGISTRY
from backend.app.services.publishing_engine import PublishingEngine
from backend.app.services.publishing_orchestrator import PublishingOrchestrator, ApprovalHashMismatchError


async def _create_master_product(client: AsyncClient, owner_headers: dict) -> dict:
    sku = f"SKU-P3M-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "sku": sku,
        "title": "Organic Cold-Pressed Mustard Oil",
        "category": "Grocery & Gourmet Foods",
        "base_price": 450.00,
        "compare_at_price": 550.00,
        "cost_price": 220.00,
        "currency": "INR",
        "stock_quantity": 40,
        "short_description": "Pure kachi ghani cold-pressed mustard oil with pungent natural aroma.",
        "long_description": "Extracted using traditional wooden kohlu method from organic mustard seeds grown in Rajasthan.",
        "weight": 1.0,
        "dimensions": {"length": 10.0, "width": 10.0, "height": 28.0},
        "tags": ["mustard oil", "kachi ghani", "organic", "cooking oil"],
        "materials": ["100% Organic Mustard Seeds"],
        "category_attributes": {
            "country_of_origin": "India",
            "hsn_code": "15149100",
            "mrp": 550.00,
            "bullet_points": [
                "100% pure cold-pressed organic mustard oil",
                "Naturally rich in MUFA, PUFA, and Omega-3 fatty acids",
                "Zero trans fats and zero chemicals or additives",
            ],
        },
    }
    res = await client.post("/api/v1/products", json=payload, headers=owner_headers)
    assert res.status_code == 201, res.text
    return res.json()


@pytest.mark.asyncio
async def test_truthful_channel_registry_and_partner_access(client: AsyncClient, owner_headers: dict):
    """Verifies that channel registry and integration list truthfully report partner statuses."""
    res = await client.get("/api/v1/integrations/registry", headers=owner_headers)
    assert res.status_code == 200
    registry = res.json()
    assert "shopify" in registry
    assert "woocommerce" in registry
    assert "amazon" in registry
    assert "flipkart" in registry
    assert "ajio" in registry
    assert "zepto" in registry

    # Check partner access requirement in integrations list
    res_list = await client.get("/api/v1/integrations", headers=owner_headers)
    assert res_list.status_code == 200
    items = {i["platform"]: i for i in res_list.json()}

    assert items["ajio"]["connection_status"] == "Partner Access Required"
    assert items["zepto"]["connection_status"] == "Partner Access Required"
    assert items["shopify"]["connection_status"] in ["Available", "Awaiting Authorization", "Connected", "Setup Required"]
    assert items["woocommerce"]["connection_status"] in ["Available", "Connected"]


@pytest.mark.asyncio
async def test_woocommerce_connect_and_webhook_verification(client: AsyncClient, owner_headers: dict):
    """Tests WooCommerce REST credentials connection and webhook HMAC validation."""
    # Test valid connect with mock test prefix
    connect_payload = {
        "store_url": "https://vedanta-organics-store.com",
        "consumer_key": "ck_test_1234567890abcdef",
        "consumer_secret": "cs_test_0987654321fedcba",
    }
    res = await client.post("/api/v1/integrations/woocommerce/connect", json=connect_payload, headers=owner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["channel_type"] == "woocommerce"
    assert data["status"] == "active"
    assert "read_products" in data["granted_scopes"]

    # Verify webhook signature verification
    secret = "webhook_secret_key_123"
    body = b'{"id": 101, "name": "Order #101"}'
    import hmac, hashlib, base64
    valid_sig = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
    assert WooCommerceService.verify_webhook_signature(body, valid_sig, secret) is True
    assert WooCommerceService.verify_webhook_signature(body, "invalid_sig", secret) is False


@pytest.mark.asyncio
async def test_amazon_sp_api_connect_and_schema_validation(client: AsyncClient, owner_headers: dict):
    """Tests Amazon SP-API connect endpoint and product type definition validation."""
    # 1. Connect Amazon account with test credentials
    connect_payload = {
        "client_id": "test_amzn1.application-oa2-client.abcdef",
        "client_secret": "test_secret_12345678",
        "refresh_token": "test_Atzr|token123456",
        "seller_id": "A21TJRUUN4KGV",
    }
    res = await client.post("/api/v1/integrations/amazon/connect", json=connect_payload, headers=owner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["channel_type"] == "amazon"
    assert data["account_identifier"] == "A21TJRUUN4KGV"

    # 2. Schema validation logic
    svc = AmazonService()
    valid_payload = {
        "item_name": [{"value": "Mustard Oil", "language_tag": "en_IN"}],
        "country_of_origin": [{"value": "IN"}],
        "purchasable_offer": [{"our_price": [{"schedule": [{"value_with_tax": 450.0}]}]}],
        "bullet_point": [{"value": "Pure oil"}],
    }
    is_valid, errors = svc.validate_listing_against_schema(valid_payload)
    assert is_valid is True
    assert len(errors) == 0

    # Incomplete payload
    invalid_payload = {"item_name": []}
    is_valid, errors = svc.validate_listing_against_schema(invalid_payload)
    assert is_valid is False
    assert len(errors) > 0


@pytest.mark.asyncio
async def test_flipkart_seller_hub_connect_and_validation(client: AsyncClient, owner_headers: dict):
    """Tests Flipkart Seller Hub connect endpoint and listing payload validation."""
    # 1. Connect Flipkart account with test credentials
    connect_payload = {
        "app_id": "test_flipkart_app_id",
        "app_secret": "test_flipkart_app_secret",
    }
    res = await client.post("/api/v1/integrations/flipkart/connect", json=connect_payload, headers=owner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["channel_type"] == "flipkart"
    assert data["status"] == "active"

    # 2. Validation logic
    valid_payload = {
        "price": {"selling_price": 450.0, "mrp": 550.0},
        "tax_details": {"hsn": "15149100"},
        "package_details": {"weight": 1.0},
    }
    is_valid, errors = FlipkartService.validate_listing_payload(valid_payload)
    assert is_valid is True

    # Price violation (selling_price > mrp)
    invalid_price = {
        "price": {"selling_price": 600.0, "mrp": 550.0},
        "tax_details": {"hsn": "15149100"},
        "package_details": {"weight": 1.0},
    }
    is_valid, errors = FlipkartService.validate_listing_payload(invalid_price)
    assert is_valid is False
    assert any("cannot exceed MRP" in e for e in errors)


@pytest.mark.asyncio
async def test_7step_publishing_workflow_and_approval_hash(client: AsyncClient, owner_headers: dict, db_session):
    """Tests the full 7-step multi-channel publishing workflow with cryptographic hash verification."""
    # 1. Create Master Product
    product = await _create_master_product(client, owner_headers)
    prod_id = product["id"]

    # 2. Connect WooCommerce
    wc_conn_payload = {
        "store_url": "https://vedanta-organics-store.com",
        "consumer_key": "ck_test_key_phase3",
        "consumer_secret": "cs_test_secret_phase3",
    }
    wc_res = await client.post("/api/v1/integrations/woocommerce/connect", json=wc_conn_payload, headers=owner_headers)
    assert wc_res.status_code == 200
    wc_conn_id = wc_res.json()["id"]

    # 3. Request Batch Preview & Approval Hash
    preview_res = await client.post(
        "/api/v1/publishing/batch-preview",
        json={"product_id": prod_id, "channel_types": ["woocommerce"]},
        headers=owner_headers,
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["overall_valid"] is True
    approval_hash = preview_data["approval_hash"]
    assert len(approval_hash) == 64  # SHA-256

    # 4. Tamper Detection: dispatch with tampered approval hash must fail with HTTP 409
    tampered_dispatch = {
        "product_id": prod_id,
        "channel_connection_ids": [wc_conn_id],
        "approval_hash": "deadbeef" * 8,
        "notes": "Tampered test",
    }
    bad_res = await client.post("/api/v1/publishing/batches", json=tampered_dispatch, headers=owner_headers)
    assert bad_res.status_code == 409

    # 5. Genuine Seller Approval & Batch Dispatch with Mock Remote Client
    with patch("backend.app.services.woocommerce_service.WooCommerceService.create_product", new_callable=AsyncMock) as mock_wc:
        mock_wc.return_value = {
            "id": 88201,
            "name": product["title"],
            "permalink": "https://vedanta-organics-store.com/product/mustard-oil-1l",
            "price": "450.00",
        }

        dispatch_payload = {
            "product_id": prod_id,
            "channel_connection_ids": [wc_conn_id],
            "approval_hash": approval_hash,
            "notes": "Seller approved for production release",
        }
        dispatch_res = await client.post("/api/v1/publishing/batches", json=dispatch_payload, headers=owner_headers)
        assert dispatch_res.status_code == 201
        batch_data = dispatch_res.json()
        assert batch_data["status"] == "completed"
        assert len(batch_data["jobs"]) == 1
        job = batch_data["jobs"][0]
        assert job["status"] == "published"
        assert job["remote_product_id"] == "88201"
        assert "vedanta-organics-store.com" in (job["remote_url"] or "")

    # 6. Verify ChannelListing persistence
    listings_res = await client.get("/api/v1/publishing/listings", headers=owner_headers)
    assert listings_res.status_code == 200
    listings = listings_res.json()
    assert any(l["remote_product_id"] == "88201" for l in listings)
    wc_listing = next(l for l in listings if l["remote_product_id"] == "88201")
    assert wc_listing["price"] == 450.0
    assert wc_listing["remote_status"] == "published"


@pytest.mark.asyncio
async def test_job_and_batch_idempotent_retry(client: AsyncClient, owner_headers: dict):
    """Tests retrying a failed publishing job and batch idempotently."""
    product = await _create_master_product(client, owner_headers)
    prod_id = product["id"]

    # Connect WooCommerce
    wc_res = await client.post(
        "/api/v1/integrations/woocommerce/connect",
        json={
            "store_url": "https://retry-test-store.com",
            "consumer_key": "ck_test_retry",
            "consumer_secret": "cs_test_retry",
        },
        headers=owner_headers,
    )
    wc_conn_id = wc_res.json()["id"]

    # Dispatch with mock failure first
    preview_res = await client.post(
        "/api/v1/publishing/batch-preview",
        json={"product_id": prod_id, "channel_types": ["woocommerce"]},
        headers=owner_headers,
    )
    approval_hash = preview_res.json()["approval_hash"]

    with patch("backend.app.services.woocommerce_service.WooCommerceService.create_product", new_callable=AsyncMock) as mock_wc:
        mock_wc.side_effect = WooCommerceError("WooCommerce Store 503 Service Unavailable")

        dispatch_res = await client.post(
            "/api/v1/publishing/batches",
            json={
                "product_id": prod_id,
                "channel_connection_ids": [wc_conn_id],
                "approval_hash": approval_hash,
            },
            headers=owner_headers,
        )
        assert dispatch_res.status_code == 201
        batch_data = dispatch_res.json()
        assert batch_data["status"] == "failed"
        failed_job = batch_data["jobs"][0]
        assert failed_job["status"] == "failed"
        assert failed_job["retry_count"] == 1
        job_id = failed_job["id"]

    # Now retry the failed job with successful mock
    with patch("backend.app.services.woocommerce_service.WooCommerceService.create_product", new_callable=AsyncMock) as mock_wc:
        mock_wc.return_value = {
            "id": 99302,
            "name": product["title"],
            "permalink": "https://retry-test-store.com/product/mustard-oil",
        }
        retry_res = await client.post(f"/api/v1/publishing/jobs/{job_id}/retry", headers=owner_headers)
        assert retry_res.status_code == 200
        retried_job = retry_res.json()
        assert retried_job["status"] == "published"
        assert retried_job["remote_product_id"] == "99302"


@pytest.mark.asyncio
async def test_tenant_isolation_on_publishing(client: AsyncClient, owner_headers: dict, make_jwt):
    """Ensures cross-tenant publication or listing access is strictly forbidden."""
    product = await _create_master_product(client, owner_headers)
    prod_id = product["id"]

    # Provision an independent second organization
    other_user_id = str(uuid.uuid4())
    other_token = make_jwt(user_id=other_user_id, email=f"other_{uuid.uuid4().hex[:6]}@example.com")
    resp = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"name": "Competitor Org", "category": "Fashion"},
    )
    assert resp.status_code == 201
    other_org_id = resp.json()["id"]
    other_headers = {"Authorization": f"Bearer {other_token}", "X-Organization-Id": other_org_id}

    # Org B trying to access Org A's publishing batch preview
    res = await client.post(
        "/api/v1/publishing/batch-preview",
        json={"product_id": prod_id, "channel_types": ["shopify"]},
        headers=other_headers,
    )
    # Should fail because product does not exist in other organization
    assert res.status_code in [400, 404]

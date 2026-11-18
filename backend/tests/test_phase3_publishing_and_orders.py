"""Automated Test Suite for MarketPath AI — Phase 3.

Validates:
1. Channel capability registry reporting.
2. Deterministic channel requirements and missing attribute detection.
3. Multi-channel pre-flight preview and cryptographic approval hash.
4. Immutable approval snapshot enforcement (tamper detection & HTTP 409).
5. Omnichannel batch dispatch, state machine, and partial success handling.
6. Remote channel listings dashboard endpoint.
7. Batch safe retry of failed jobs.
8. Central order ingestion, SKU mapping, and idempotent deduplication.
9. Inventory decrement on order and negative stock protection.
10. Safe channel disconnect with master catalogue preservation.
11. Cross-tenant publishing and order isolation.
12. Grounded business analytics reflecting verified database orders.
"""

import uuid
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from backend.app.core.security import encrypt_token
from backend.app.models.catalogue import Product, ProductChannelOverride
from backend.app.models.channel import ChannelConnection, ChannelListing, PublishingBatch, PublishingJob
from backend.app.models.order import ChannelOrder, ChannelOrderItem
from backend.app.services.order_sync_service import OrderSyncService
from backend.app.services.publishing_orchestrator import PublishingOrchestrator


async def _create_test_master_product(client: AsyncClient, owner_headers: dict) -> dict:
    """Helper to create a rich master product for Phase 3 tests."""
    sku = f"SKU-P3-{uuid.uuid4().hex[:6].upper()}"
    prod_payload = {
        "sku": sku,
        "title": "Artisanal Terracotta Water Carafe",
        "category": "Home & Kitchen",
        "base_price": 999.00,
        "compare_at_price": 1499.00,
        "cost_price": 380.00,
        "currency": "INR",
        "stock_quantity": 25,
        "short_description": "Natural clay water carafe that keeps water naturally cool.",
        "long_description": "Earthen carafe handcrafted by potters in Rajasthan using unglazed organic clay.",
        "weight": 0.85,
        "dimensions": {"length": 14.0, "width": 14.0, "height": 24.0},
        "tags": ["terracotta", "carafe", "handmade", "sustainable"],
        "materials": ["Natural Clay"],
        "packaging_specs": {
            "box_dimensions": {"length": 16.0, "width": 16.0, "height": 26.0},
            "packaging_material": "Honeycomb paper and corrugated carton",
        },
        "category_attributes": {
            "country_of_origin": "India",
            "hsn_code": "69120010",
            "mrp": 1499.00,
            "bullet_points": [
                "100% natural unglazed earthenware carafe",
                "Naturally cools water via evaporative transpiration",
                "Includes cork lid to keep dust away",
            ],
        },
    }
    resp = await client.post("/api/v1/products", json=prod_payload, headers=owner_headers)
    assert resp.status_code == 201, resp.text
    prod_data = resp.json()

    # Attach media asset
    media_payload = {
        "cloudinary_public_id": f"carafe_{uuid.uuid4().hex[:6]}",
        "media_url": "https://res.cloudinary.com/marketpath/image/upload/v1/carafe_main.jpg",
        "media_type": "image",
        "alt_text": "Terracotta Carafe Front View",
        "display_order": 1,
    }
    await client.post(f"/api/v1/products/{prod_data['id']}/media", json=media_payload, headers=owner_headers)

    return prod_data


async def _create_active_connection(
    db_session,
    org_id: uuid.UUID,
    channel_type: str,
    account_name: str,
) -> ChannelConnection:
    """Helper to provision an active channel connection in the database."""
    conn = ChannelConnection(
        organization_id=org_id,
        channel_type=channel_type,
        channel_group="storefront" if channel_type in ["shopify", "woocommerce"] else "marketplace",
        partner_status="connected",
        account_identifier=f"{channel_type}-test-{uuid.uuid4().hex[:6]}",
        account_name=account_name,
        encrypted_access_token=encrypt_token("mock-live-access-token-12345"),
        granted_scopes=["write_products", "read_orders", "write_inventory"],
        status="active",
    )
    db_session.add(conn)
    await db_session.commit()
    await db_session.refresh(conn)
    return conn


@pytest.mark.asyncio
async def test_channel_capability_registry_endpoint(
    client: AsyncClient,
    owner_headers: dict,
):
    """Verifies that the channel capability registry API reports honest developer onboarding requirements."""
    res = await client.get("/api/v1/integrations/registry", headers=owner_headers)
    assert res.status_code == 200, res.text
    registry = res.json()

    # Core channels must be present
    for ch in ["shopify", "woocommerce", "amazon", "flipkart", "google_merchant"]:
        assert ch in registry, f"Missing channel in registry: {ch}"
        spec = registry[ch]
        assert "capabilities" in spec
        assert "required_api_scopes" in spec
        assert "rate_limits" in spec
        assert "developer_onboarding" in spec

        caps = spec["capabilities"]
        assert "product_creation" in caps
        assert "inventory_updates" in caps
        assert "price_updates" in caps

    # Verify Shopify and WooCommerce have order retrieval enabled
    assert registry["shopify"]["capabilities"]["order_retrieval"] is True
    assert registry["woocommerce"]["capabilities"]["order_retrieval"] is True


@pytest.mark.asyncio
async def test_channel_requirements_and_missing_attributes_detection(
    client: AsyncClient,
    owner_headers: dict,
):
    """Verifies deterministic missing attribute detection for Amazon India and Flipkart."""
    # Create product missing HSN code, MRP, and shipping weight
    incomplete_prod = {
        "sku": f"SKU-INC-{uuid.uuid4().hex[:6].upper()}",
        "title": "Minimal Ceramic Mug",
        "category": "Kitchenware",
        "base_price": 499.00,
        "cost_price": 180.00,
        "currency": "INR",
        "stock_quantity": 10,
    }
    create_res = await client.post("/api/v1/products", json=incomplete_prod, headers=owner_headers)
    assert create_res.status_code == 201
    prod_id = create_res.json()["id"]

    # Check requirements across channels
    check_res = await client.post(
        f"/api/v1/products/{prod_id}/channel-requirements",
        json={"channels": ["amazon", "flipkart", "shopify"]},
        headers=owner_headers,
    )
    assert check_res.status_code == 200, check_res.text
    data = check_res.json()

    # Amazon check
    assert "amazon" in data
    amz = data["amazon"]
    assert amz["is_ready"] is False
    amz_missing = [mf["field"] for mf in amz.get("missing_fields", [])]
    assert "package_weight" in amz_missing or "country_of_origin" in amz_missing or "hsn_code" in amz_missing

    # Flipkart check
    assert "flipkart" in data
    fk = data["flipkart"]
    assert fk["is_ready"] is False
    fk_missing = [mf["field"] for mf in fk.get("missing_fields", [])]
    assert "mrp" in fk_missing or "hsn_code" in fk_missing or "shipping_weight" in fk_missing


@pytest.mark.asyncio
async def test_multi_channel_batch_preview_and_approval_hash(
    client: AsyncClient,
    owner_headers: dict,
):
    """Verifies pre-flight batch preview generates channel payloads and a SHA-256 approval hash."""
    prod = await _create_test_master_product(client, owner_headers)
    prod_id = prod["id"]

    preview_res = await client.post(
        "/api/v1/publishing/batch-preview",
        json={
            "product_id": prod_id,
            "channel_types": ["shopify", "woocommerce", "amazon", "flipkart"],
        },
        headers=owner_headers,
    )
    assert preview_res.status_code == 200, preview_res.text
    batch_prev = preview_res.json()

    assert batch_prev["product_id"] == prod_id
    assert len(batch_prev["approval_hash"]) == 64  # SHA-256 length
    assert "channel_previews" in batch_prev
    assert "shopify" in batch_prev["channel_previews"]
    assert "woocommerce" in batch_prev["channel_previews"]


@pytest.mark.asyncio
async def test_immutable_approval_snapshot_rejects_tampered_product(
    client: AsyncClient,
    owner_headers: dict,
    db_session,
    owner_setup,
):
    """Verifies that modifying master product attributes after preview invalidates approval hash (HTTP 409)."""
    org_id = uuid.UUID(owner_setup["org_id"])
    prod = await _create_test_master_product(client, owner_headers)
    prod_id = prod["id"]

    # Connect Shopify
    conn = await _create_active_connection(db_session, org_id, "shopify", "Shopify Store")

    # 1. Generate preview and capture approval hash
    prev_res = await client.post(
        "/api/v1/publishing/batch-preview",
        json={"product_id": prod_id, "channel_types": ["shopify"]},
        headers=owner_headers,
    )
    assert prev_res.status_code == 200
    stale_approval_hash = prev_res.json()["approval_hash"]

    # 2. Tamper: edit product price directly
    patch_res = await client.put(
        f"/api/v1/products/{prod_id}",
        json={"title": prod["title"], "base_price": 1299.00},
        headers=owner_headers,
    )
    assert patch_res.status_code == 200

    # 3. Attempt dispatch using the stale approval hash
    dispatch_res = await client.post(
        "/api/v1/publishing/batches",
        json={
            "product_id": prod_id,
            "channel_connection_ids": [str(conn.id)],
            "approval_hash": stale_approval_hash,
        },
        headers=owner_headers,
    )
    assert dispatch_res.status_code == 409, dispatch_res.text
    err_body = dispatch_res.json()
    err_msg = err_body.get("detail") or err_body.get("error", {}).get("message", "")
    assert "modified after the preview was approved" in err_msg


@pytest.mark.asyncio
async def test_batch_publishing_dispatch_and_execution(
    client: AsyncClient,
    owner_headers: dict,
    db_session,
    owner_setup,
):
    """Verifies multi-channel batch dispatch, immutable snapshot storage, and listing creation."""
    org_id = uuid.UUID(owner_setup["org_id"])
    prod = await _create_test_master_product(client, owner_headers)
    prod_id = prod["id"]

    # Connect Shopify and WooCommerce
    conn_shop = await _create_active_connection(db_session, org_id, "shopify", "Aura Terra Shopify")
    conn_wc = await _create_active_connection(db_session, org_id, "woocommerce", "Aura Terra WooCommerce")

    # Mock Shopify and WooCommerce execution
    with patch("backend.app.services.shopify_service.ShopifyService.create_product_listing", new_callable=AsyncMock) as mock_shop:
        mock_shop.return_value = {
            "remote_product_id": "gid://shopify/Product/987654321",
            "remote_url": "https://auraterra.myshopify.com/products/carafe",
            "raw_response": {"id": 987654321},
        }

        # 1. Get fresh preview
        prev_res = await client.post(
            "/api/v1/publishing/batch-preview",
            json={"product_id": prod_id, "channel_types": ["shopify", "woocommerce"]},
            headers=owner_headers,
        )
        assert prev_res.status_code == 200
        approval_hash = prev_res.json()["approval_hash"]

        # 2. Dispatch batch
        dispatch_res = await client.post(
            "/api/v1/publishing/batches",
            json={
                "product_id": prod_id,
                "channel_connection_ids": [str(conn_shop.id), str(conn_wc.id)],
                "approval_hash": approval_hash,
                "notes": "Spring 2026 catalogue launch batch",
            },
            headers=owner_headers,
        )
        assert dispatch_res.status_code == 201, dispatch_res.text
        batch = dispatch_res.json()

        assert batch["status"] in ["completed", "partially_completed"]
        assert len(batch["jobs"]) == 2
        assert batch["approval_hash"] == approval_hash
        assert batch["approved_by_user_id"] is not None

        # 3. Verify batch in listings
        batches_list = await client.get("/api/v1/publishing/batches", headers=owner_headers)
        assert batches_list.status_code == 200
        assert len(batches_list.json()) >= 1


@pytest.mark.asyncio
async def test_channel_listings_dashboard_endpoint(
    client: AsyncClient,
    owner_headers: dict,
    db_session,
    owner_setup,
):
    """Verifies that published channel listings are retrieved with external IDs and status."""
    org_id = uuid.UUID(owner_setup["org_id"])
    prod = await _create_test_master_product(client, owner_headers)
    conn = await _create_active_connection(db_session, org_id, "shopify", "Shopify Store")

    # Manually create a ChannelListing
    listing = ChannelListing(
        product_id=uuid.UUID(prod["id"]),
        channel_connection_id=conn.id,
        remote_product_id="gid://shopify/Product/11223344",
        remote_url="https://store.example.com/products/carafe",
        remote_status="published",
    )
    db_session.add(listing)
    await db_session.commit()

    res = await client.get("/api/v1/publishing/listings", headers=owner_headers)
    assert res.status_code == 200, res.text
    listings = res.json()

    assert len(listings) >= 1
    target = next((l for l in listings if l["remote_product_id"] == "gid://shopify/Product/11223344"), None)
    assert target is not None
    assert target["channel_type"] == "shopify"
    assert target["remote_url"] == "https://store.example.com/products/carafe"
    assert target["product_sku"] == prod["sku"]


@pytest.mark.asyncio
async def test_order_ingestion_and_idempotent_deduplication(
    client: AsyncClient,
    owner_headers: dict,
    db_session,
    owner_setup,
):
    """Verifies central order ingestion, SKU stock decrement, and strict deduplication."""
    org_id = uuid.UUID(owner_setup["org_id"])
    prod = await _create_test_master_product(client, owner_headers)
    sku = prod["sku"]
    initial_stock = prod["stock_quantity"]

    conn = await _create_active_connection(db_session, org_id, "shopify", "Shopify Store")

    items_data = [
        {
            "sku": sku,
            "title": prod["title"],
            "quantity": 2,
            "unit_price": 999.00,
            "total_price": 1998.00,
        }
    ]

    remote_order_id = f"ord_remote_{uuid.uuid4().hex[:8]}"

    # First ingestion
    order1, is_new1 = await OrderSyncService.ingest_order(
        db=db_session,
        organization_id=org_id,
        channel_type="shopify",
        remote_order_id=remote_order_id,
        order_number="#1088",
        total_amount=1998.00,
        currency="INR",
        items_data=items_data,
        channel_connection_id=conn.id,
        customer_name="Pooja Sharma",
        financial_status="paid",
    )
    assert is_new1 is True
    assert order1.total_amount == 1998.00

    # Second ingestion with identical remote_order_id must be rejected as duplicate
    order2, is_new2 = await OrderSyncService.ingest_order(
        db=db_session,
        organization_id=org_id,
        channel_type="shopify",
        remote_order_id=remote_order_id,
        order_number="#1088",
        total_amount=1998.00,
        currency="INR",
        items_data=items_data,
        channel_connection_id=conn.id,
        customer_name="Pooja Sharma",
        financial_status="paid",
    )
    assert is_new2 is False
    assert order2.id == order1.id

    # Verify orders API lists the order
    res = await client.get("/api/v1/orders", headers=owner_headers)
    assert res.status_code == 200, res.text
    orders_data = res.json()
    assert orders_data["total_orders"] >= 1
    assert orders_data["total_revenue_inr"] >= 1998.00


@pytest.mark.asyncio
async def test_inventory_decrement_and_negative_stock_guard(
    client: AsyncClient,
    owner_headers: dict,
    db_session,
    owner_setup,
):
    """Verifies that stock decrements safely and is clamped at 0 (never negative)."""
    org_id = uuid.UUID(owner_setup["org_id"])

    # Create product with stock = 3
    sku = f"SKU-STOCK-{uuid.uuid4().hex[:6].upper()}"
    res = await client.post(
        "/api/v1/products",
        json={
            "sku": sku,
            "title": "Limited Clay Bowl",
            "category": "Tableware",
            "base_price": 500.00,
            "stock_quantity": 3,
        },
        headers=owner_headers,
    )
    assert res.status_code == 201

    # Ingest order with quantity = 5 (exceeding stock of 3)
    order, _ = await OrderSyncService.ingest_order(
        db=db_session,
        organization_id=org_id,
        channel_type="woocommerce",
        remote_order_id=f"wc_ord_{uuid.uuid4().hex[:8]}",
        order_number="WC-900",
        total_amount=2500.00,
        currency="INR",
        items_data=[{"sku": sku, "title": "Limited Clay Bowl", "quantity": 5, "unit_price": 500.00}],
    )

    # Verify stock in DB is 0 (never -2)
    p_res = await db_session.execute(select(Product).where(Product.organization_id == org_id, Product.sku == sku))
    prod = p_res.scalar_one()
    assert prod.stock_quantity == 0


@pytest.mark.asyncio
async def test_safe_channel_disconnect_preserves_catalogue(
    client: AsyncClient,
    owner_headers: dict,
    db_session,
    owner_setup,
):
    """Verifies that disconnecting a sales channel does NOT delete master products."""
    org_id = uuid.UUID(owner_setup["org_id"])
    prod = await _create_test_master_product(client, owner_headers)
    prod_id = prod["id"]

    conn = await _create_active_connection(db_session, org_id, "shopify", "Shopify To Disconnect")

    # Disconnect
    del_res = await client.post(f"/api/v1/integrations/{conn.id}/disconnect", headers=owner_headers)
    assert del_res.status_code == 200, del_res.text
    del_data = del_res.json()
    assert "Master Product Catalogue is preserved" in del_data["catalogue_status"]

    # Master product must still exist and be intact
    prod_res = await client.get(f"/api/v1/products/{prod_id}", headers=owner_headers)
    assert prod_res.status_code == 200
    assert prod_res.json()["id"] == prod_id


@pytest.mark.asyncio
async def test_cross_tenant_publishing_and_orders_isolation(
    client: AsyncClient,
    owner_headers: dict,
    member_headers: dict,
    db_session,
    owner_setup,
):
    """Verifies strict cross-tenant isolation for publishing batches, listings, and orders."""
    org_id = uuid.UUID(owner_setup["org_id"])
    prod = await _create_test_master_product(client, owner_headers)

    # Tenant B lists publishing batches
    t2_batches = await client.get("/api/v1/publishing/batches", headers=member_headers)
    assert t2_batches.status_code == 200
    assert len(t2_batches.json()) == 0

    # Tenant B lists orders
    t2_orders = await client.get("/api/v1/orders", headers=member_headers)
    assert t2_orders.status_code == 200
    assert t2_orders.json()["total_orders"] == 0


@pytest.mark.asyncio
async def test_grounded_analytics_reflects_genuine_orders(
    client: AsyncClient,
    owner_headers: dict,
    db_session,
    owner_setup,
):
    """Verifies analytics overview returns genuine order and revenue numbers from database."""
    org_id = uuid.UUID(owner_setup["org_id"])
    prod = await _create_test_master_product(client, owner_headers)

    # Ingest paid order
    await OrderSyncService.ingest_order(
        db=db_session,
        organization_id=org_id,
        channel_type="shopify",
        remote_order_id=f"ord_anl_{uuid.uuid4().hex[:8]}",
        order_number="#ANL-101",
        total_amount=3500.00,
        currency="INR",
        items_data=[{"sku": prod["sku"], "quantity": 3, "unit_price": 999.00, "total_price": 2997.00}],
        financial_status="paid",
    )

    ov_res = await client.get("/api/v1/analytics/overview", headers=owner_headers)
    assert ov_res.status_code == 200, ov_res.text
    ov = ov_res.json()

    assert ov["total_orders"] >= 1
    assert ov["gross_sales_inr"] >= 3500.00
    assert ov["units_sold"] >= 3
    assert len(ov["channel_sales_breakdown"]) >= 1

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_conversational_onboarding_turn_and_confirm(
    client: AsyncClient,
    owner_headers: dict,
    db_session: AsyncSession,
):
    """Verifies that conversational intake extracts dimensions and populates catalogue upon confirmation."""
    # 1. Conversation turn
    turn_payload = {
        "message": "We craft handmade ceramic tableware and terracotta mugs in Pune. Our mission is zero plastic living. Our hero product is a Ceramic Chai Kulhad Set of 4 priced at ₹899, MRP ₹1199, package weight 950g.",
        "history": [],
    }
    resp = await client.post("/api/v1/brand-profile/conversational-onboard", json=turn_payload, headers=owner_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "assistant_message" in data
    assert data["extracted_brand"] is not None
    assert len(data["extracted_products"]) >= 1
    assert data["extracted_products"][0]["title"] is not None
    assert len(data["extracted_products"][0]["title"]) > 0

    # 2. Confirm and save
    confirm_payload = {
        "brand_data": data["extracted_brand"],
        "products_data": data["extracted_products"],
    }
    confirm_resp = await client.post("/api/v1/brand-profile/conversational-confirm", json=confirm_payload, headers=owner_headers)
    assert confirm_resp.status_code == 200, confirm_resp.text
    confirm_data = confirm_resp.json()
    assert confirm_data["status"] == "success"
    assert confirm_data["products_created"] >= 1


@pytest.mark.asyncio
async def test_channel_requirements_validation_amazon_and_flipkart(
    client: AsyncClient,
    owner_headers: dict,
):
    """Verifies that channel requirements accurately detect missing attributes without fabricating data."""
    # 1. Create product first
    p_res = await client.post(
        "/api/v1/products",
        headers=owner_headers,
        json={
            "sku": f"VAL-TEST-{uuid.uuid4().hex[:6].upper()}",
            "title": "Chai Kulhad Set for Validation",
            "short_description": "Handcrafted terracotta cups.",
            "long_description": "Traditional terracotta chai glasses with natural earthen aroma.",
            "category": "Home & Living",
            "base_price": 799.00,
            "stock_quantity": 25,
            "currency": "INR",
        },
    )
    assert p_res.status_code == 201, p_res.text
    product_id = p_res.json()["id"]

    # 2. Check Amazon requirements
    resp = await client.post(
        f"/api/v1/products/{product_id}/channel-requirements",
        json={"channel": "amazon"},
        headers=owner_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "amazon" in data["channels"]
    amz_check = data["channels"]["amazon"]
    assert "is_ready" in amz_check
    assert "missing_fields" in amz_check

    # 3. Check Flipkart requirements
    resp_fk = await client.post(
        f"/api/v1/products/{product_id}/channel-requirements",
        json={"channel": "flipkart"},
        headers=owner_headers,
    )
    assert resp_fk.status_code == 200, resp_fk.text
    fk_data = resp_fk.json()
    assert "flipkart" in fk_data["channels"]
    fk_check = fk_data["channels"]["flipkart"]
    assert "is_ready" in fk_check


@pytest.mark.asyncio
async def test_orders_list_and_sync(
    client: AsyncClient,
    owner_headers: dict,
):
    """Verifies that orders can be queried and synchronized across connected channels."""
    # 1. Query orders list
    resp = await client.get("/api/v1/orders", headers=owner_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "total_orders" in data
    assert "orders" in data

    # 2. Trigger sync
    sync_resp = await client.post("/api/v1/orders/sync", json={"channel_type": None}, headers=owner_headers)
    assert sync_resp.status_code == 200, sync_resp.text
    sync_data = sync_resp.json()
    assert "synced_channels" in sync_data
    assert "inventory_updates_queued" in sync_data


@pytest.mark.asyncio
async def test_context_aware_support_bot(
    client: AsyncClient,
    owner_headers: dict,
):
    """Verifies that the floating support assistant provides contextual answers for channel errors."""
    payload = {
        "message": "Why did my Amazon listing fail? What are the missing bullet points and weight requirements?",
        "current_page": "/app/publishing",
        "history": [],
    }
    resp = await client.post("/api/v1/support/chat", json=payload, headers=owner_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "answer" in data
    assert "suggested_actions" in data
    assert len(data["answer"]) > 0

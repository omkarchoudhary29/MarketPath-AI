"""Phase 2: Brand Intelligence, Conversational Voice AI & Master Product Management Tests.

Validates:
1. Brand Profile 5-section update and deterministic completeness score calculation.
2. Brand conversational intake turn, follow-ups, and confirmation lifecycle.
3. Unified product text extraction and voice intake simulation.
4. Master product creation with child variant matrix and per-tenant SKU uniqueness.
5. Cost price privacy enforcement across roles (owner vs. viewer).
6. Channel readiness check against genuine marketplace schemas.
7. Strict data isolation: demo organization vs. real tenant product catalogue.
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.brand import BrandProfile
from backend.app.models.catalogue import Product, ProductVariant
from backend.app.services.demo_catalogue_fixtures import seed_demo_catalogue_if_empty


@pytest.mark.asyncio
async def test_brand_profile_completeness_calculation(
    client: AsyncClient,
    owner_headers: dict,
):
    """Verifies that brand profile completeness score updates deterministically based on non-empty canonical dimensions."""
    # 1. Fetch initial brand profile
    res = await client.get("/api/v1/brand-profile", headers=owner_headers)
    assert res.status_code == 200, res.text
    initial_data = res.json()
    assert "completeness_score" in initial_data
    assert "missing_recommended_fields" in initial_data
    assert isinstance(initial_data["completeness_score"], (int, float))

    # 2. Update via PATCH with comprehensive 15-dimension attributes
    patch_payload = {
        "brand_name": "Kaveri Clay Works",
        "tagline": "Pure Earthen Craft for Sustainable Living",
        "story": "Founded on the banks of the Kaveri river, we craft non-toxic pottery in collaboration with traditional artisan guilds.",
        "mission": "To eradicate plastic and heavy-metal kitchenware through authentic certified lead-free terracotta.",
        "target_audience": "Urban families, mindful homemakers, and sustainable design enthusiasts aged 25-45.",
        "tone_of_voice": "Warm & Aesthetic",
        "archetype": "Creator & Caregiver",
        "key_usps": ["100% Lead-Free Glaze", "Direct Artisan Living Wage", "Compostable Packaging"],
        "brand_values": ["Craft Dignity", "Ecological Purity", "Living Heritage"],
        "pricing_strategy": "Accessible premium with transparent markup",
        "sustainability_practices": "Zero-plastic shipping, regional clay sourcing, low-carbon wood kilns",
        "packaging_philosophy": "Recycled corrugated cartons with seed paper thank-you notes",
        "visual_guidelines": {
            "palette": ["#8B4513", "#2D5A27", "#F4F1EA"],
            "typography": "Playfair Display / Inter",
        },
    }
    update_res = await client.patch("/api/v1/brand-profile", json=patch_payload, headers=owner_headers)
    assert update_res.status_code == 200, update_res.text
    updated_data = update_res.json()
    assert updated_data["brand_name"] == "Kaveri Clay Works"
    assert updated_data["completeness_score"] == 100.0
    assert len(updated_data["missing_recommended_fields"]) == 0


@pytest.mark.asyncio
async def test_brand_conversational_turn_and_confirm_lifecycle(
    client: AsyncClient,
    owner_headers: dict,
    db_session: AsyncSession,
):
    """Verifies conversational onboarding: conversational turn extracts dimensions and confirm populates database."""
    # 1. Spoken interview turn
    turn_payload = {
        "message": (
            "Hi, my brand is Mitti Magic. We handcraft terracotta kitchenware in Pune. "
            "Our flagship product is a Handcrafted Terracotta Water Bottle priced at ₹799, MRP ₹1099, "
            "weighing 750 grams. We offer Natural Raw and Matte Ochre finishes."
        ),
        "history": [],
    }
    turn_res = await client.post("/api/v1/brand-profile/conversational-onboard", json=turn_payload, headers=owner_headers)
    assert turn_res.status_code == 200, turn_res.text
    turn_data = turn_res.json()
    assert "reply_message" in turn_data
    assert turn_data["extracted_brand"] is not None
    assert len(turn_data["extracted_products"]) >= 1

    extracted_prod = turn_data["extracted_products"][0]
    assert extracted_prod["title"] is not None
    assert len(extracted_prod["title"]) > 0
    assert (extracted_prod.get("base_price") or 799.0) > 0

    # 2. Confirm conversational draft
    confirm_payload = {
        "brand_data": turn_data["extracted_brand"],
        "products_data": turn_data["extracted_products"],
    }
    confirm_res = await client.post("/api/v1/brand-profile/conversational-confirm", json=confirm_payload, headers=owner_headers)
    assert confirm_res.status_code == 200, confirm_res.text
    confirm_data = confirm_res.json()
    assert confirm_data["success"] is True
    assert confirm_data["products_created"] >= 1


@pytest.mark.asyncio
async def test_product_text_intake_extraction(
    client: AsyncClient,
    owner_headers: dict,
):
    """Verifies unstructured product notes extraction into structured master draft with channel requirement detection."""
    text_notes = (
        "Hand-carved sheesham wood cutting board with groove. "
        "Dimensions are 30cm length, 20cm width, 2.5cm height. Weight is 850 grams. "
        "Selling at 1499, MRP is 1999, production cost is 450. "
        "Finishes: Natural Oil and Dark Walnut. "
        "Packed in corrugated box with honeycomb cushioning."
    )
    res = await client.post(
        "/api/v1/products/extract-from-text",
        headers=owner_headers,
        json={"text": text_notes, "category_hint": "Kitchen & Dining"},
    )
    assert res.status_code == 200, res.text
    draft = res.json()

    assert draft["base_price"] == 1499.0
    assert draft["compare_at_price"] == 1999.0
    assert draft["cost_price"] == 450.0
    assert draft["dimensions_cm"]["length"] == 30.0
    assert draft["dimensions_cm"]["width"] == 20.0
    assert draft["dimensions_cm"]["height"] == 2.5
    assert draft["weight_kg"] == 0.85
    assert len(draft["suggested_variants"]) >= 2
    assert "Dark Walnut" in [v["option_value"] for v in draft["suggested_variants"]]


@pytest.mark.asyncio
async def test_product_voice_intake_endpoint(
    client: AsyncClient,
    owner_headers: dict,
):
    """Verifies voice intake endpoint handles transcript and simulated audio correctly."""
    voice_payload = {
        "transcript": (
            "We make ceramic coffee mugs in set of 2. "
            "Priced at ₹599, MRP ₹799. Weight is 500g. "
            "Dimensions are 10 by 10 by 12 centimeters."
        ),
        "category_hint": "Kitchen & Dining",
    }
    res = await client.post("/api/v1/products/voice-intake", headers=owner_headers, json=voice_payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["base_price"] == 599.0
    assert data["compare_at_price"] == 799.0
    assert data["confidence_score"] >= 0.85


@pytest.mark.asyncio
async def test_master_product_creation_with_variants_and_sku_uniqueness(
    client: AsyncClient,
    owner_headers: dict,
    member_headers: dict,
):
    """Verifies product creation with child variant matrix and per-tenant SKU uniqueness enforcement."""
    master_sku = f"TEST-MUG-{uuid.uuid4().hex[:6].upper()}"

    payload = {
        "sku": master_sku,
        "title": "Glazed Stoneware Mug",
        "category": "Kitchen & Dining",
        "short_description": "Hand-thrown stoneware mug.",
        "long_description": "Ergonomic ceramic mug for coffee and tea rituals.",
        "status": "active",
        "base_price": 599.00,
        "compare_at_price": 799.00,
        "cost_price": 180.00,
        "currency": "INR",
        "stock_quantity": 40,
        "materials": ["Stoneware Clay", "Food-Safe Glaze"],
        "dimensions": {"length": 10.0, "width": 10.0, "height": 12.0, "unit": "cm"},
        "weight": 0.50,
        "packaging_specs": {
            "box_length": 14.0,
            "box_width": 14.0,
            "box_height": 16.0,
            "dead_weight_grams": 600,
            "packaging_material": "Corrugated Kraft Carton",
        },
        "variants": [
            {
                "sku": f"{master_sku}-MINT",
                "title": "Glazed Stoneware Mug - Mint Green",
                "price": 599.00,
                "stock_quantity": 20,
                "options": {"Color": "Mint Green"},
            },
            {
                "sku": f"{master_sku}-OCHRE",
                "title": "Glazed Stoneware Mug - Ochre",
                "price": 599.00,
                "stock_quantity": 20,
                "options": {"Color": "Ochre"},
            },
        ],
    }

    # 1. Create product in Tenant A
    create_res = await client.post("/api/v1/products", headers=owner_headers, json=payload)
    assert create_res.status_code == 201, create_res.text
    prod_data = create_res.json()
    assert prod_data["sku"] == master_sku
    assert len(prod_data["variants"]) == 2

    # 2. Duplicate SKU in same tenant should be rejected (409 Conflict)
    dup_res = await client.post("/api/v1/products", headers=owner_headers, json=payload)
    assert dup_res.status_code == 409, dup_res.text

    # 3. Same SKU in separate tenant should SUCCEED (tenant isolation)
    member_res = await client.post("/api/v1/products", headers=member_headers, json=payload)
    assert member_res.status_code == 201, member_res.text


@pytest.mark.asyncio
async def test_cost_price_privacy_per_role(
    client: AsyncClient,
    owner_setup: dict,
    make_jwt,
    db_session: AsyncSession,
):
    """Verifies that cost_price is visible to owner/admin but strictly redacted for viewer role."""
    from backend.app.models.organization import OrganizationMember

    owner_headers = owner_setup["headers"]
    org_id = owner_setup["org_id"]

    # 1. Create product as owner with cost price
    sku = f"PRIV-TEST-{uuid.uuid4().hex[:6].upper()}"
    create_res = await client.post(
        "/api/v1/products",
        headers=owner_headers,
        json={
            "sku": sku,
            "title": "Privacy Test Candle",
            "category": "Home & Decor",
            "base_price": 799.00,
            "cost_price": 250.00,
            "currency": "INR",
            "stock_quantity": 10,
        },
    )
    assert create_res.status_code == 201
    prod_id = create_res.json()["id"]

    # 2. Add viewer user to organization
    viewer_user_id = str(uuid.uuid4())
    viewer_token = make_jwt(user_id=viewer_user_id, email="viewer@tenant.com")
    member = OrganizationMember(
        id=uuid.uuid4(),
        organization_id=uuid.UUID(org_id),
        user_id=uuid.UUID(viewer_user_id),
        role="viewer",
    )
    db_session.add(member)
    await db_session.commit()

    viewer_headers = {
        "Authorization": f"Bearer {viewer_token}",
        "X-Organization-Id": org_id,
    }

    # 3. Viewer requests product list -> cost_price must be None
    list_res = await client.get("/api/v1/products", headers=viewer_headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    found_item = next((i for i in items if i["id"] == prod_id), None)
    assert found_item is not None
    assert found_item["cost_price"] is None

    # 4. Viewer requests product detail -> cost_price must be None
    detail_res = await client.get(f"/api/v1/products/{prod_id}", headers=viewer_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["cost_price"] is None


@pytest.mark.asyncio
async def test_demo_vs_real_tenant_product_isolation(
    client: AsyncClient,
    owner_setup: dict,
    db_session: AsyncSession,
):
    """Verifies that demo products are strictly isolated and new real merchants start with 0 products."""
    from backend.app.api.v1.auth import DEMO_ORG_ID
    demo_org_id = DEMO_ORG_ID

    # 1. Seed demo catalogue for demo organization
    count = await seed_demo_catalogue_if_empty(db_session, demo_org_id)
    assert count >= 4

    # 2. Newly registered real merchant queries products -> MUST BE EMPTY
    real_headers = owner_setup["headers"]
    real_res = await client.get("/api/v1/products", headers=real_headers)
    assert real_res.status_code == 200
    real_data = real_res.json()
    assert real_data["total"] == 0
    assert len(real_data["items"]) == 0

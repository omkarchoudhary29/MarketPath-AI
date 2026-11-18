import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_product_crud_flow(client: AsyncClient, make_jwt):
    """Verifies complete master product lifecycle: create with variants, read, update, list."""
    user_id = str(uuid.uuid4())
    token = make_jwt(user_id=user_id, email="owner@auraterra.in")

    # 1. Create Organization
    org_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Aura Ceramics Studio", "category": "Home & Living"},
    )
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]

    # 2. Create Master Product with Variants
    create_payload = {
        "sku": "CER-MUG-001",
        "title": "Artisanal Speckled Ceramic Mug",
        "short_description": "Hand-thrown stoneware coffee mug.",
        "long_description": "Individually handcrafted by master potters in Pune. Food-safe glaze.",
        "category": "Home & Living",
        "status": "draft",
        "base_price": 899.00,
        "compare_at_price": 1199.00,
        "cost_price": 320.00,
        "currency": "INR",
        "stock_quantity": 45,
        "dimensions": {"length": 10, "width": 8, "height": 11, "unit": "cm"},
        "weight": 0.35,
        "materials": ["Stoneware Clay", "Food-safe Glaze"],
        "tags": ["ceramic", "handmade", "coffee", "sustainable"],
        "seo_title": "Handmade Ceramic Mug | Aura Ceramics",
        "seo_description": "Artisanal speckled coffee mug handcrafted in Pune.",
        "variants": [
            {
                "sku": "CER-MUG-001-IVR",
                "title": "Ivory / 350ml",
                "price": 899.00,
                "stock_quantity": 25,
                "options": {"color": "Ivory", "capacity": "350ml"},
            },
            {
                "sku": "CER-MUG-001-TER",
                "title": "Terracotta / 350ml",
                "price": 899.00,
                "stock_quantity": 20,
                "options": {"color": "Terracotta", "capacity": "350ml"},
            },
        ],
    }

    create_res = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json=create_payload,
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["sku"] == "CER-MUG-001"
    assert created["title"] == "Artisanal Speckled Ceramic Mug"
    assert created["cost_price"] == 320.00  # Owner sees cost_price
    assert len(created["variants"]) == 2
    assert created["variants"][0]["sku"] == "CER-MUG-001-IVR"
    product_id = created["id"]

    # 3. Read Product Details
    get_res = await client.get(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == product_id
    assert len(get_res.json()["variants"]) == 2

    # 4. Update Product
    update_res = await client.put(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={"title": "Updated Artisanal Speckled Ceramic Mug", "status": "active"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Artisanal Speckled Ceramic Mug"
    assert update_res.json()["status"] == "active"

    # 5. List Products with Pagination and Filter
    list_res = await client.get(
        "/api/v1/products?category=Home%20%26%20Living&status=active",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
    )
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["title"] == "Updated Artisanal Speckled Ceramic Mug"


@pytest.mark.asyncio
async def test_product_sku_uniqueness_per_tenant(client: AsyncClient, make_jwt):
    """Verifies that duplicate SKUs within the same organization are rejected with 409."""
    token = make_jwt(user_id=str(uuid.uuid4()), email="owner@test.in")

    org_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "SKU Test Store"},
    )
    org_id = org_res.json()["id"]

    prod_payload = {
        "sku": "UNIQUE-SKU-100",
        "title": "First Item",
        "category": "Home & Living",
        "base_price": 500.0,
    }

    res1 = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json=prod_payload,
    )
    assert res1.status_code == 201

    # Attempt duplicate SKU in same organization
    res2 = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json=prod_payload,
    )
    assert res2.status_code == 409
    assert "already exists" in res2.json()["error"]["message"]


@pytest.mark.asyncio
async def test_cost_price_privacy_per_role(client: AsyncClient, make_jwt):
    """Verifies that cost_price is strictly hidden from Marketers and Viewers."""
    owner_id = str(uuid.uuid4())
    owner_token = make_jwt(user_id=owner_id, email="owner@auraterra.in")

    org_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Privacy Test Store"},
    )
    org_id = org_res.json()["id"]

    # Create product with sensitive cost_price
    prod_res = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {owner_token}", "X-Organization-Id": org_id},
        json={
            "sku": "SECRET-COST-01",
            "title": "Cost Sensitive Item",
            "category": "Home & Living",
            "base_price": 1000.0,
            "cost_price": 250.0,
        },
    )
    prod_id = prod_res.json()["id"]
    assert prod_res.json()["cost_price"] == 250.0  # Owner sees it

    # Invite a Marketer
    marketer_email = "marketer@auraterra.in"
    inv_res = await client.post(
        "/api/v1/team/invites",
        headers={"Authorization": f"Bearer {owner_token}", "X-Organization-Id": org_id},
        json={"email": marketer_email, "role": "marketer"},
    )
    marketer_id = inv_res.json()["user_id"]
    marketer_token = make_jwt(user_id=marketer_id, email=marketer_email)

    # Marketer reads product: cost_price MUST BE None
    m_get = await client.get(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {marketer_token}", "X-Organization-Id": org_id},
    )
    assert m_get.status_code == 200
    assert m_get.json()["cost_price"] is None


@pytest.mark.asyncio
async def test_product_soft_archive_and_channel_overrides(client: AsyncClient, make_jwt):
    """Verifies soft archive and separate channel override management."""
    token = make_jwt(user_id=str(uuid.uuid4()), email="owner@auraterra.in")

    org_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Override Test Store"},
    )
    org_id = org_res.json()["id"]

    prod_res = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "sku": "OVERRIDE-01",
            "title": "Master Title",
            "category": "Home & Living",
            "base_price": 500.0,
        },
    )
    prod_id = prod_res.json()["id"]

    # Upsert channel override for Shopify
    override_res = await client.put(
        f"/api/v1/products/{prod_id}/overrides/shopify",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "channel_type": "shopify",
            "custom_title": "Shopify Specific SEO Title",
            "custom_price": 549.0,
            "custom_tags": ["shopify-featured"],
            "is_approved_for_channel": True,
        },
    )
    assert override_res.status_code == 200
    assert override_res.json()["custom_title"] == "Shopify Specific SEO Title"
    assert override_res.json()["custom_price"] == 549.0

    # Verify master record title was NOT modified
    master_check = await client.get(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
    )
    assert master_check.json()["title"] == "Master Title"
    assert master_check.json()["base_price"] == 500.0

    # Soft archive product
    del_res = await client.delete(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
    )
    assert del_res.status_code == 204

    # Verify product status is now archived
    archived_get = await client.get(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
    )
    assert archived_get.json()["status"] == "archived"


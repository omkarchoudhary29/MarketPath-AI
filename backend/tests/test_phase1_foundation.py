"""Phase 1 Foundation, Authentication, Security, and Public Assistant Tests."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_registration_creates_clean_org_and_owner(client: AsyncClient):
    """Verifies that new real merchant registration creates user, organization, owner role, and clean zero-state workspace."""
    email = f"artisan_{uuid.uuid4().hex[:6]}@craftstudio.in"
    reg_payload = {
        "brand_name": "Sanskriti Pottery Studio",
        "category": "Home & Living / Decor",
        "full_name": "Rohan Sharma",
        "email": email,
        "password": "SecurePassword123!",
        "website": "https://sanskrithipottery.in",
    }

    reg_res = await client.post("/api/v1/auth/register-company", json=reg_payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert data["account_type"] == "company"
    assert data["user"]["email"] == email
    assert data["user"]["full_name"] == "Rohan Sharma"
    assert data["organization"]["role"] == "owner"
    assert "sanskriti-pottery-studio" in data["organization"]["slug"]

    token = data["access_token"]
    org_id = data["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-Id": org_id}

    # Verify brand profile was auto-initialized
    brand_res = await client.get("/api/v1/brand-profile", headers=headers)
    assert brand_res.status_code == 200
    assert brand_res.json()["brand_name"] == "Sanskriti Pottery Studio"

    # Verify zero-state purity: 0 products, 0 orders
    prod_res = await client.get("/api/v1/products", headers=headers)
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    assert prod_data.get("items") == [] or prod_data == []
    assert prod_data.get("total", 0) == 0

    orders_res = await client.get("/api/v1/orders", headers=headers)
    assert orders_res.status_code == 200
    orders_data = orders_res.json()
    assert orders_data.get("total_orders", 0) == 0
    assert orders_data.get("total_revenue_inr", 0.0) == 0.0
    assert orders_data.get("orders", []) == []


@pytest.mark.asyncio
async def test_unregistered_email_login_rejected(client: AsyncClient):
    """Verifies that an unregistered random email is strictly rejected rather than silently aliased to demo."""
    login_payload = {
        "email": f"unknown_merchant_{uuid.uuid4().hex[:6]}@example.com",
        "password": "SomePassword123",
        "account_type": "company",
    }
    res = await client.post("/api/v1/auth/login-account", json=login_payload)
    assert res.status_code == 401
    assert "sign up" in res.json()["error"]["message"].lower() or "invalid" in res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_demo_account_explicit_session(client: AsyncClient):
    """Verifies that the demo session endpoint has been permanently disabled under Phase 2 security mandates."""
    res = await client.post("/api/v1/auth/demo-session", json={"role": "owner", "as_admin": False})
    assert res.status_code == 403
    assert "removed" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_multi_org_switching_and_revalidation(client: AsyncClient, make_jwt):
    """Verifies that a user belonging to multiple organizations can access each verified organization."""
    user_id = str(uuid.uuid4())
    token = make_jwt(user_id=user_id, email=f"multistore_{uuid.uuid4().hex[:6]}@example.com")
    auth_header = {"Authorization": f"Bearer {token}"}

    # Create Store 1
    res1 = await client.post("/api/v1/organizations", headers=auth_header, json={"name": "Kashmir Pashmina Works"})
    assert res1.status_code == 201
    org1_id = res1.json()["id"]

    # Create Store 2
    res2 = await client.post("/api/v1/organizations", headers=auth_header, json={"name": "Ladakh Organic Honey"})
    assert res2.status_code == 201
    org2_id = res2.json()["id"]

    # List organizations
    list_res = await client.get("/api/v1/organizations", headers=auth_header)
    assert list_res.status_code == 200
    org_ids = [o["id"] for o in list_res.json()]
    assert org1_id in org_ids
    assert org2_id in org_ids

    # Query active Store 1
    s1_res = await client.get("/api/v1/organizations/active", headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org1_id})
    assert s1_res.status_code == 200
    assert s1_res.json()["name"] == "Kashmir Pashmina Works"

    # Query active Store 2
    s2_res = await client.get("/api/v1/organizations/active", headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org2_id})
    assert s2_res.status_code == 200
    assert s2_res.json()["name"] == "Ladakh Organic Honey"

    # Attack: User attempts to supply a non-member organization ID
    random_org_id = str(uuid.uuid4())
    fraud_res = await client.get("/api/v1/organizations/active", headers={"Authorization": f"Bearer {token}", "X-Organization-Id": random_org_id})
    assert fraud_res.status_code in [403, 404]


@pytest.mark.asyncio
async def test_public_assistant_faq_grounding(client: AsyncClient):
    """Verifies that unauthenticated visitors can query platform FAQs with zero authentication credentials."""
    # Channel capabilities
    res_channels = await client.post("/api/v1/support/public-chat", json={"message": "What channels are supported?"})
    assert res_channels.status_code == 200
    ans_channels = res_channels.json()
    assert "channel" in ans_channels["answer"].lower() or "marketpath" in ans_channels["answer"].lower() or "shopify" in ans_channels["answer"].lower()
    assert len(ans_channels["suggested_actions"]) > 0

    # Consultation booking
    res_consult = await client.post("/api/v1/support/public-chat", json={"message": "How do I book a consultation?"})
    assert res_consult.status_code == 200
    ans_consult = res_consult.json()
    assert "consult" in ans_consult["answer"].lower()
    actions = [a["action_url"] for a in ans_consult["suggested_actions"]]
    assert "/free-consultation" in actions

    # Registration info
    res_reg = await client.post("/api/v1/support/public-chat", json={"message": "How do I sign up for MarketPath?"})
    assert res_reg.status_code == 200
    ans_reg = res_reg.json()
    assert any(term in ans_reg["answer"].lower() for term in ["workspace", "regist", "sign", "account"])
    reg_actions = [a["action_url"] for a in ans_reg["suggested_actions"]]
    assert "/signup" in reg_actions


@pytest.mark.asyncio
async def test_public_assistant_strictly_rejects_private_data_queries(client: AsyncClient):
    """Critical: Unauthenticated visitors asking about private orders, stock, or revenue receive boundary rejection."""
    res = await client.post("/api/v1/support/public-chat", json={"message": "Where is my order and what is my inventory stock?"})
    assert res.status_code == 200
    data = res.json()
    assert "workspace after you sign in" in data["answer"].lower()
    assert data["data_sources_used"] == ["Public Assistant Security Boundary"]
    action_urls = [a["action_url"] for a in data["suggested_actions"]]
    assert "/login" in action_urls


@pytest.mark.asyncio
async def test_direct_id_manipulation_cross_tenant_blocked(client: AsyncClient, make_jwt):
    """Verifies that User A cannot read or modify User B's product by guessing/manipulating product ID."""
    token_a = make_jwt(user_id=str(uuid.uuid4()), email="seller_a@craft.in")
    org_a_res = await client.post("/api/v1/organizations", headers={"Authorization": f"Bearer {token_a}"}, json={"name": "Org A Ceramics"})
    org_a_id = org_a_res.json()["id"]
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-Id": org_a_id}

    # User A creates a product
    parent_sku = f"KULHAD-M-{uuid.uuid4().hex[:6]}"
    prod_a_res = await client.post(
        "/api/v1/products",
        headers=headers_a,
        json={
            "sku": parent_sku,
            "title": "Terracotta Chai Kulhad",
            "category": "Kitchen & Dining",
            "base_price": 299.0,
            "variants": [{"title": "Standard Set of 4", "sku": f"KULHAD-{uuid.uuid4().hex[:4]}", "price": 299.0, "inventory_quantity": 25}],
        },
    )
    assert prod_a_res.status_code == 201
    prod_a_id = prod_a_res.json()["id"]

    # User B logs in to a different organization
    token_b = make_jwt(user_id=str(uuid.uuid4()), email="seller_b@textiles.in")
    org_b_res = await client.post("/api/v1/organizations", headers={"Authorization": f"Bearer {token_b}"}, json={"name": "Org B Silks"})
    org_b_id = org_b_res.json()["id"]
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-Id": org_b_id}

    # Attack: User B attempts to fetch User A's product by ID
    attack_res = await client.get(f"/api/v1/products/{prod_a_id}", headers=headers_b)
    assert attack_res.status_code == 404  # Must be 404 Not Found within Tenant B's boundary (no data leakage)

    # Attack: User B attempts to update User A's product via PUT
    attack_put = await client.put(f"/api/v1/products/{prod_a_id}", headers=headers_b, json={"title": "Hacked Product Title"})
    assert attack_put.status_code in [404, 403, 422]

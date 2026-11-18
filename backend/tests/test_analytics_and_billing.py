import datetime
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.billing import Payment, Plan, ServiceOrder, Subscription
from backend.app.models.catalogue import Product
from backend.app.models.marketing import Campaign, CampaignMetricsDaily, ExternalCampaign
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import UserProfile


@pytest.mark.asyncio
async def test_analytics_overview_deterministic_aggregation(
    client: AsyncClient, owner_headers: dict, owner_org_id: str, db_session: AsyncSession
):
    """Verifies that Analytics overview correctly computes deterministic totals and formulas."""
    org_uuid = uuid.UUID(owner_org_id)

    # Create products
    p1 = Product(organization_id=org_uuid, title="Handcrafted Ceramic Vase", sku="VASE-01", category="Home Decor", status="active", base_price=1200)
    p2 = Product(organization_id=org_uuid, title="Speckled Mug", sku="MUG-01", category="Home Decor", status="active", base_price=650)
    db_session.add_all([p1, p2])

    # Create campaign and metrics
    camp = Campaign(
        organization_id=org_uuid,
        name="Diwali Festive Push",
        objective="conversions",
        channel="meta_ads",
        total_budget=5000.0,
        daily_budget_limit=500.0,
        start_date=datetime.date.today() - datetime.timedelta(days=10),
        status="active",
    )
    db_session.add(camp)
    await db_session.flush()

    ext_camp = ExternalCampaign(
        campaign_id=camp.id,
        ad_account_id=uuid.uuid4(),
        platform="meta_ads",
        remote_campaign_id="act_meta_12345",
        remote_status="ACTIVE",
    )
    db_session.add(ext_camp)
    await db_session.flush()

    metrics = CampaignMetricsDaily(
        external_campaign_id=ext_camp.id,
        date=datetime.date.today() - datetime.timedelta(days=3),
        spend=1500.0,
        impressions=10000,
        clicks=250,
        reach=7500,
        conversions=15,
        conversion_value=6000.0,
    )
    db_session.add(metrics)
    await db_session.commit()

    resp = await client.get("/api/v1/analytics/overview?time_range=Last 30 Days", headers=owner_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Deterministic verification
    assert data["total_products"] == 2
    assert data["active_products"] == 2
    assert data["total_spend"] == 1500.0
    assert data["total_impressions"] == 10000
    assert data["total_clicks"] == 250
    assert data["total_reach"] == 7500
    assert data["total_conversions"] == 15
    assert data["total_conversion_value"] == 6000.0
    # CTR = (250 / 10000) * 100 = 2.5%
    assert data["average_ctr"] == 2.5
    # CPC = 1500 / 250 = 6.0
    assert data["average_cpc"] == 6.0
    # ROAS = 6000 / 1500 = 4.0
    assert data["roas"] == 4.0
    assert data["currency"] == "INR"
    assert data["timezone"] == "Asia/Kolkata"


@pytest.mark.asyncio
async def test_ai_analytics_assistant_grounding(client: AsyncClient, owner_headers: dict):
    """Verifies that AI analytics assistant returns grounded response and references actual numbers."""
    resp = await client.post(
        "/api/v1/analytics/ai-assistant",
        headers=owner_headers,
        json={
            "question": "Which channel generated the most clicks this month?",
            "time_range": "Last 30 Days",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "question" in data
    assert "answer" in data
    assert "grounding_data" in data
    assert data["grounding_data"]["timezone"] == "Asia/Kolkata"
    assert data["grounding_data"]["currency"] == "INR"


@pytest.mark.asyncio
async def test_billing_plans_and_usage_meters(client: AsyncClient, owner_headers: dict):
    """Verifies plan listing, default subscription provisioning, and usage meters."""
    # 1. Get plans
    plans_resp = await client.get("/api/v1/billing/plans")
    assert plans_resp.status_code == 200
    plans = plans_resp.json()
    assert len(plans) >= 3
    plan_names = [p["name"] for p in plans]
    assert "Starter" in plan_names
    assert "Growth" in plan_names
    assert "Scale" in plan_names

    # 2. Get tenant subscription
    sub_resp = await client.get("/api/v1/billing/subscription", headers=owner_headers)
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert sub_data["status"] == "active"
    assert sub_data["plan"]["name"] in ["Growth", "Starter"]

    # 3. Get usage meters
    usage_resp = await client.get("/api/v1/billing/usage", headers=owner_headers)
    assert usage_resp.status_code == 200
    usage = usage_resp.json()
    assert "active_skus" in usage
    assert "connected_channels" in usage
    assert "ai_generations" in usage


@pytest.mark.asyncio
async def test_billing_checkout_and_server_side_verification(
    client: AsyncClient, owner_headers: dict, db_session: AsyncSession
):
    """Verifies payment checkout initiation, server-side signature validation, and upgrade activation."""
    # Seed or fetch Scale plan
    plans_resp = await client.get("/api/v1/billing/plans")
    plans = plans_resp.json()
    scale_plan = next(p for p in plans if p["name"] == "Scale")
    scale_plan_id = scale_plan["id"]

    # 1. Initiate checkout
    checkout_resp = await client.post(
        "/api/v1/billing/checkout",
        headers=owner_headers,
        json={"plan_id": scale_plan_id, "gateway": "razorpay"},
    )
    assert checkout_resp.status_code == 200, checkout_resp.text
    chk = checkout_resp.json()
    assert chk["amount_inr"] == 5999.0
    assert chk["currency"] == "INR"
    assert chk["plan_name"] == "Scale"
    order_id = chk["order_id"]

    # 2. Server-side verification with test signature
    verify_resp = await client.post(
        "/api/v1/billing/verify",
        headers=owner_headers,
        json={
            "gateway": "razorpay",
            "order_id": order_id,
            "payment_id": f"pay_{uuid.uuid4().hex[:10]}",
            "signature": "sig_test_verified_12345",
            "plan_id": scale_plan_id,
        },
    )
    assert verify_resp.status_code == 200, verify_resp.text
    sub = verify_resp.json()
    assert sub["status"] == "active"
    assert sub["plan"]["name"] == "Scale"
    assert sub["plan"]["max_active_skus"] == 500

    # 3. Check payment record in payments table
    pmt_resp = await client.get("/api/v1/billing/payments", headers=owner_headers)
    assert pmt_resp.status_code == 200
    payments = pmt_resp.json()
    assert len(payments) == 1
    assert payments[0]["amount_inr"] == 5999.0
    assert payments[0]["status"] == "success"


@pytest.mark.asyncio
async def test_backend_quota_enforcement_skus(
    client: AsyncClient, owner_headers: dict, owner_org_id: str, db_session: AsyncSession
):
    """Verifies that adding products beyond plan max_active_skus raises 402 Payment Required."""
    org_uuid = uuid.UUID(owner_org_id)

    # Assign a micro plan with max_active_skus = 1
    plan = Plan(
        name=f"Micro_{uuid.uuid4().hex[:4]}",
        monthly_price_inr=499,
        max_active_skus=1,
        max_connected_channels=1,
        ai_generation_monthly_quota=10,
        is_active=True,
    )
    db_session.add(plan)
    await db_session.flush()

    sub = await db_session.execute(select(Subscription).where(Subscription.organization_id == org_uuid))
    cur_sub = sub.scalar_one_or_none()
    if cur_sub:
        cur_sub.plan_id = plan.id
    else:
        new_sub = Subscription(
            organization_id=org_uuid,
            plan_id=plan.id,
            status="active",
            current_period_start=datetime.datetime.now(datetime.timezone.utc),
            current_period_end=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30),
            cancel_at_period_end=False,
        )
        db_session.add(new_sub)

    # Add 1 existing product
    p = Product(organization_id=org_uuid, title="Single Allowed Product", sku="SOLO-01", category="Home Decor", status="active", base_price=500)
    db_session.add(p)
    await db_session.commit()

    # Try to add a 2nd product
    resp = await client.post(
        "/api/v1/products",
        headers=owner_headers,
        json={
            "title": "Second Product Overflow",
            "sku": "OVERFLOW-02",
            "base_price": 999.0,
            "category": "Home Decor",
            "status": "draft",
        },
    )
    # Blocked by quota check with 402 Payment Required
    assert resp.status_code == 402
    err_msg = resp.json().get("error", {}).get("message") or resp.json().get("detail", "")
    assert "Active SKU quota exceeded" in err_msg


@pytest.mark.asyncio
async def test_managed_service_order_lifecycle(
    client: AsyncClient, owner_headers: dict, make_jwt: callable
):
    """Verifies seller requesting a managed service and operator administrative updates."""
    # 1. Seller creates service order request
    req_resp = await client.post(
        "/api/v1/services/orders",
        headers=owner_headers,
        json={
            "service_type": "guided_onboarding",
            "scope_description": "We need help migrating 45 SKUs from WooCommerce to Shopify with Instagram linking.",
            "target_budget_inr": 2999,
        },
    )
    assert req_resp.status_code == 201, req_resp.text
    order_data = req_resp.json()
    order_id = order_data["id"]
    assert order_data["status"] == "requested"
    assert order_data["quoted_price_inr"] == 2999

    # 2. Admin token
    admin_id = str(uuid.uuid4())
    admin_token = make_jwt(user_id=admin_id, email="super_admin@marketpath.ai", is_platform_admin=True)

    # Provision user profile first so require_platform_admin succeeds
    await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})

    # Admin views service orders
    admin_list_resp = await client.get(
        "/api/v1/admin/service-orders",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_list_resp.status_code == 200
    orders = admin_list_resp.json()
    assert any(o["id"] == order_id for o in orders)

    # 3. Admin updates service order to in_progress with deliverable notes
    update_resp = await client.put(
        f"/api/v1/admin/service-orders/{order_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "status": "in_progress",
            "deliverables_notes": "Assigned to operator Priya K. Migration scheduled for Thursday.",
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["status"] == "in_progress"
    assert "Priya K" in updated["deliverables_notes"]


@pytest.mark.asyncio
async def test_platform_admin_rbac_isolation(
    client: AsyncClient, owner_headers: dict, make_jwt: callable
):
    """Verifies that non-admin users cannot access /api/v1/admin/* endpoints."""
    # Regular owner fails with 403 Forbidden
    reg_resp = await client.get("/api/v1/admin/overview", headers=owner_headers)
    assert reg_resp.status_code == 403
    err = reg_resp.json().get("error", {}).get("message") or reg_resp.json().get("detail", "")
    assert "Platform Administrator" in err

    # Admin user succeeds
    admin_id = str(uuid.uuid4())
    admin_token = make_jwt(user_id=admin_id, email="super_admin2@marketpath.ai", is_platform_admin=True)
    await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})

    adm_resp = await client.get("/api/v1/admin/overview", headers={"Authorization": f"Bearer {admin_token}"})
    assert adm_resp.status_code == 200
    data = adm_resp.json()
    assert "total_organizations" in data
    assert "publishing_success_rate" in data
    assert data["operator_email"] == "super_admin2@marketpath.ai"


@pytest.mark.asyncio
async def test_payment_webhooks_signature_and_deduplication(client: AsyncClient):
    """Verifies HMAC signature check and idempotent deduplication on Razorpay webhook endpoint."""
    event_id = f"evt_test_{uuid.uuid4().hex[:12]}"
    payload = {
        "entity": "event",
        "event_id": event_id,
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{uuid.uuid4().hex[:8]}",
                    "amount": 249900,
                    "currency": "INR",
                    "status": "captured",
                }
            }
        },
    }

    # Valid test signature
    valid_resp_1 = await client.post(
        "/api/v1/webhooks/razorpay",
        headers={"X-Razorpay-Signature": "test_razorpay_sig"},
        json=payload,
    )
    assert valid_resp_1.status_code == 200
    res1 = valid_resp_1.json()
    assert res1["processed"] is True

    # 2. Duplicate webhook with same event_id is idempotently deduplicated
    valid_resp_2 = await client.post(
        "/api/v1/webhooks/razorpay",
        headers={"X-Razorpay-Signature": "test_razorpay_sig"},
        json=payload,
    )
    assert valid_resp_2.status_code == 200
    res2 = valid_resp_2.json()
    assert res2["processed"] is False
    assert "Duplicate event" in res2["message"]

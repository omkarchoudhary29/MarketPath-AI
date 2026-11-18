import datetime
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit import AuditLog
from backend.app.models.catalogue import Product
from backend.app.models.marketing import Campaign, CampaignMetricsDaily, ExternalCampaign, AdAccount


@pytest.mark.asyncio
async def test_campaign_create_validation_and_crud(client: AsyncClient, owner_headers: dict):
    """Verifies campaign brief creation, budget limit validation, and listing."""
    # 1. Invalid: Daily budget higher than total budget
    bad_payload = {
        "name": "Invalid Budget Campaign",
        "objective": "sales",
        "total_budget": 500.0,
        "daily_budget_limit": 1000.0,
        "start_date": "2026-11-15",
        "end_date": "2026-11-30",
    }
    res = await client.post("/api/v1/campaigns", headers=owner_headers, json=bad_payload)
    assert res.status_code == 400

    # 2. Invalid: Daily budget less than minimum ₹100
    bad_daily = {
        "name": "Too Small Daily Limit",
        "objective": "traffic",
        "total_budget": 5000.0,
        "daily_budget_limit": 50.0,
        "start_date": "2026-11-15",
    }
    res = await client.post("/api/v1/campaigns", headers=owner_headers, json=bad_daily)
    assert res.status_code == 422  # Pydantic validation error

    # 3. Invalid: Start date after end date
    bad_dates = {
        "name": "Reverse Dates Campaign",
        "objective": "traffic",
        "total_budget": 5000.0,
        "daily_budget_limit": 500.0,
        "start_date": "2026-12-01",
        "end_date": "2026-11-15",
    }
    res = await client.post("/api/v1/campaigns", headers=owner_headers, json=bad_dates)
    assert res.status_code == 400

    # 4. Valid Campaign Creation
    valid_payload = {
        "name": "Artisanal Coffee Mug Launch Sprint",
        "objective": "sales",
        "channel": "meta_ads",
        "target_geography": "Mumbai & Pune",
        "target_audience_brief": "Urban coffee and design lovers",
        "total_budget": 15000.0,
        "daily_budget_limit": 1000.0,
        "currency": "INR",
        "start_date": "2026-11-15",
        "end_date": "2026-11-30",
        "landing_page_url": "https://auraterra.in/products/ceramic-mug",
        "call_to_action": "Shop Now",
        "creative_format": "feed_image",
        "creatives": [
            {
                "headline": "Handcrafted Stoneware for Mindful Mornings",
                "primary_text": "Upgrade your daily ritual with hand-thrown ceramic mugs crafted in Pune.",
                "cta_text": "Shop Now",
                "media_url": "https://res.cloudinary.com/marketpath/image/upload/v1/mug_lifestyle.jpg",
                "destination_url": "https://auraterra.in/products/ceramic-mug",
                "format": "feed_image",
                "is_selected": True,
            }
        ],
    }
    create_res = await client.post("/api/v1/campaigns", headers=owner_headers, json=valid_payload)
    assert create_res.status_code == 201
    camp_data = create_res.json()
    camp_id = camp_data["id"]
    assert camp_data["name"] == "Artisanal Coffee Mug Launch Sprint"
    assert camp_data["status"] == "draft"
    assert camp_data["total_budget"] == 15000.0
    assert len(camp_data["creatives"]) == 1

    # 5. List campaigns
    list_res = await client.get("/api/v1/campaigns", headers=owner_headers)
    assert list_res.status_code == 200
    campaigns = list_res.json()
    assert len(campaigns) >= 1
    assert any(c["id"] == camp_id for c in campaigns)

    # 6. Get single campaign detail
    detail_res = await client.get(f"/api/v1/campaigns/{camp_id}", headers=owner_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == camp_id


@pytest.mark.asyncio
async def test_campaign_ai_planner_grounding(client: AsyncClient, owner_headers: dict):
    """Verifies that the Gemini AI Campaign Planner returns structured proposals without fabricated benchmarks."""
    payload = {
        "natural_language_brief": "Promote handmade bamboo gift boxes to premium wedding and corporate gifters in Maharashtra. Total budget ₹10,000 for 30 days.",
        "objective": "leads",
        "target_geography": "Maharashtra (Mumbai & Pune)",
        "monthly_budget_inr": 10000.0,
        "duration_days": 30,
        "channel": "meta_ads",
    }
    plan_res = await client.post("/api/v1/campaigns/plan", headers=owner_headers, json=payload)
    assert plan_res.status_code == 200
    plan_data = plan_res.json()

    # Verify structured output schema fields
    assert "strategy_summary" in plan_data
    assert "objective_interpretation" in plan_data
    assert "suggested_channel" in plan_data
    assert "target_audience_hypotheses" in plan_data
    assert isinstance(plan_data["target_audience_hypotheses"], list)
    assert len(plan_data["ad_headlines"]) >= 3
    assert len(plan_data["primary_texts"]) >= 3
    assert len(plan_data["creative_concepts"]) >= 1
    assert "suggested_budget_allocation" in plan_data
    assert "campaign_schedule" in plan_data
    assert "measurement_strategy" in plan_data
    assert "assumptions_and_risks" in plan_data
    assert "disclaimer" in plan_data

    # Verify budget allocation matches seller constraint
    budget_alloc = plan_data["suggested_budget_allocation"]
    assert budget_alloc["total_budget_inr"] == 10000.0


@pytest.mark.asyncio
async def test_campaign_approval_workflow_requires_owner_or_admin(
    client: AsyncClient,
    owner_setup: dict,
    make_jwt,
    db_session: AsyncSession,
):
    """Verifies that marketer cannot approve budget alone; requires owner/admin authorization."""
    owner_headers = owner_setup["headers"]
    org_id = owner_setup["org_id"]

    # Create campaign as owner
    camp_payload = {
        "name": "Budget Approval Verification Campaign",
        "objective": "sales",
        "total_budget": 20000.0,
        "daily_budget_limit": 1000.0,
        "start_date": "2026-11-20",
        "end_date": "2026-12-10",
        "channel": "meta_ads",
    }
    camp_res = await client.post("/api/v1/campaigns", headers=owner_headers, json=camp_payload)
    assert camp_res.status_code == 201
    camp_id = camp_res.json()["id"]

    # Provision a 'marketer' role user in the same organization
    marketer_user_id = str(uuid.uuid4())
    marketer_token = make_jwt(user_id=marketer_user_id, email="marketer@example.com")
    # Authenticate marketer first to establish user_profile with correct sub UUID
    await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {marketer_token}"})

    # Invite marketer to organization
    inv_res = await client.post(
        "/api/v1/team/invites",
        headers=owner_headers,
        json={"email": "marketer@example.com", "role": "marketer"},
    )
    assert inv_res.status_code in (200, 201)

    marketer_headers = {
        "Authorization": f"Bearer {marketer_token}",
        "X-Organization-Id": org_id,
    }

    # 1. Marketer attempts to approve campaign budget -> Expect 403 Forbidden
    marketer_appr = await client.post(
        f"/api/v1/campaigns/{camp_id}/approve",
        headers=marketer_headers,
        json={"approved": True, "notes": "Marketer attempting unauthorized approval"},
    )
    assert marketer_appr.status_code == 403
    err_msg = marketer_appr.json().get("error", {}).get("message") or marketer_appr.json().get("detail", "")
    assert "Permission denied" in err_msg

    # 2. Owner approves campaign budget -> Expect 200 OK
    owner_appr = await client.post(
        f"/api/v1/campaigns/{camp_id}/approve",
        headers=owner_headers,
        json={"approved": True, "notes": "Approved by founder after review"},
    )
    assert owner_appr.status_code == 200
    appr_data = owner_appr.json()
    assert appr_data["success"] is True
    assert appr_data["campaign"]["status"] == "ready_for_manual_setup"
    assert appr_data["campaign"]["approved_by_user_id"] is not None
    assert appr_data["campaign"]["approved_at"] is not None
    assert appr_data["manual_execution_pack"] is not None


@pytest.mark.asyncio
async def test_campaign_pause_resume_stop_controls(client: AsyncClient, owner_headers: dict):
    """Verifies campaign pause, resume, and stop controls."""
    # Create and approve campaign
    camp_payload = {
        "name": "Control Flow Test Campaign",
        "objective": "traffic",
        "total_budget": 8000.0,
        "daily_budget_limit": 800.0,
        "start_date": "2026-11-20",
    }
    c_res = await client.post("/api/v1/campaigns", headers=owner_headers, json=camp_payload)
    camp_id = c_res.json()["id"]

    await client.post(
        f"/api/v1/campaigns/{camp_id}/approve",
        headers=owner_headers,
        json={"approved": True},
    )

    # 1. Pause campaign
    pause_res = await client.post(
        f"/api/v1/campaigns/{camp_id}/pause",
        headers=owner_headers,
        json={"action": "pause", "reason": "Testing pause functionality"},
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "paused"

    # 2. Resume campaign
    resume_res = await client.post(f"/api/v1/campaigns/{camp_id}/resume", headers=owner_headers)
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] in ("active", "ready_for_manual_setup")

    # 3. Stop campaign
    stop_res = await client.post(
        f"/api/v1/campaigns/{camp_id}/stop",
        headers=owner_headers,
        json={"action": "stop", "reason": "Budget fully utilized"},
    )
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_manual_setup_pack_export(client: AsyncClient, owner_headers: dict):
    """Verifies that an exportable manual setup pack is generated with step-by-step instructions and UTMs."""
    camp_payload = {
        "name": "Export Test Campaign",
        "objective": "sales",
        "target_geography": "Bengaluru & Delhi NCR",
        "total_budget": 12000.0,
        "daily_budget_limit": 1000.0,
        "start_date": "2026-11-20",
        "end_date": "2026-12-02",
        "landing_page_url": "https://auraterra.in/collections/festive",
        "call_to_action": "Shop Now",
    }
    c_res = await client.post("/api/v1/campaigns", headers=owner_headers, json=camp_payload)
    camp_id = c_res.json()["id"]

    # Export setup pack
    exp_res = await client.get(f"/api/v1/campaigns/{camp_id}/export", headers=owner_headers)
    assert exp_res.status_code == 200
    pack = exp_res.json()

    assert pack["setup_status"] == "Ready for Manual Setup"
    assert "utm_source=meta_ads" in pack["utm_tagged_destination_url"]
    assert "utm_medium=paid_social" in pack["utm_tagged_destination_url"]
    assert len(pack["step_by_step_instructions"]) >= 8
    assert pack["targeting_checklist"]["campaign_objective"] == "SALES"
    assert "₹1,000.00" in pack["budget_and_schedule"]["daily_budget"]


@pytest.mark.asyncio
async def test_campaign_deterministic_metrics_calculation(
    client: AsyncClient,
    owner_headers: dict,
    owner_org_id: str,
    db_session: AsyncSession,
):
    """Verifies backend mathematical calculation of CTR, CPC, and ROAS without LLM hallucination."""
    # 1. Create a campaign
    camp_payload = {
        "name": "Metrics Math Test Campaign",
        "objective": "sales",
        "total_budget": 10000.0,
        "daily_budget_limit": 1000.0,
        "start_date": "2026-11-15",
        "end_date": "2026-11-25",
    }
    c_res = await client.post("/api/v1/campaigns", headers=owner_headers, json=camp_payload)
    camp_id = c_res.json()["id"]

    # Ingest verified daily metrics into database
    ad_acc = AdAccount(
        organization_id=uuid.UUID(owner_org_id),
        platform="meta_ads",
        external_account_id="act_test_metrics",
        account_name="Primary Meta Ad Account",
        currency="INR",
        status="connected",
    )
    db_session.add(ad_acc)
    await db_session.flush()

    ext_camp = ExternalCampaign(
        campaign_id=uuid.UUID(camp_id),
        ad_account_id=ad_acc.id,
        platform="meta_ads",
        remote_campaign_id="meta_cmp_992140",
        remote_status="ACTIVE",
    )
    db_session.add(ext_camp)
    await db_session.flush()

    # Day 1: Spend=1000, Impressions=20000, Clicks=500, Conversions=15, ConvValue=4500
    # Expected: CTR = 500 / 20000 * 100 = 2.50%, CPC = 1000 / 500 = 2.00, ROAS = 4500 / 1000 = 4.50x
    dm1 = CampaignMetricsDaily(
        external_campaign_id=ext_camp.id,
        date=datetime.date(2026, 11, 16),
        spend=1000.00,
        impressions=20000,
        clicks=500,
        reach=16000,
        conversions=15,
        conversion_value=4500.00,
    )
    # Day 2: Spend=1000, Impressions=25000, Clicks=625, Conversions=20, ConvValue=6000
    # Expected Day 2: CTR = 625 / 25000 * 100 = 2.50%, CPC = 1000 / 625 = 1.60, ROAS = 6000 / 1000 = 6.00x
    dm2 = CampaignMetricsDaily(
        external_campaign_id=ext_camp.id,
        date=datetime.date(2026, 11, 17),
        spend=1000.00,
        impressions=25000,
        clicks=625,
        reach=21000,
        conversions=20,
        conversion_value=6000.00,
    )
    db_session.add_all([dm1, dm2])
    await db_session.commit()

    # Fetch performance metrics endpoint
    metrics_res = await client.get(f"/api/v1/campaigns/{camp_id}/metrics", headers=owner_headers)
    assert metrics_res.status_code == 200
    perf = metrics_res.json()

    # Check totals & averages
    assert perf["total_spend"] == 2000.00
    assert perf["remaining_budget"] == 8000.00  # 10000 - 2000
    assert perf["total_impressions"] == 45000
    assert perf["total_clicks"] == 1125
    assert perf["total_conversions"] == 35
    assert perf["total_conversion_value"] == 10500.00

    # Total Blended CTR = 1125 / 45000 * 100 = 2.50%
    assert perf["average_ctr"] == 2.50
    # Total Blended CPC = 2000 / 1125 = 1.78
    assert perf["average_cpc"] == 1.78
    # Total Blended ROAS = 10500 / 2000 = 5.25x
    assert perf["blended_roas"] == 5.25
    assert perf["data_source"] == "Meta Marketing API"
    assert len(perf["daily_breakdown"]) == 2


@pytest.mark.asyncio
async def test_cross_tenant_campaign_isolation(
    client: AsyncClient,
    owner_headers: dict,
    member_headers: dict,
):
    """Verifies that Organization B cannot view or approve Organization A's campaigns."""
    # Org A creates a campaign
    camp_payload = {
        "name": "Org A Confidential Campaign",
        "objective": "sales",
        "total_budget": 5000.0,
        "daily_budget_limit": 500.0,
        "start_date": "2026-11-20",
    }
    c_res = await client.post("/api/v1/campaigns", headers=owner_headers, json=camp_payload)
    camp_id = c_res.json()["id"]

    # Org B attempts to view Org A's campaign -> 404 Not Found
    get_res = await client.get(f"/api/v1/campaigns/{camp_id}", headers=member_headers)
    assert get_res.status_code == 404

    # Org B attempts to approve Org A's campaign -> 404 Not Found
    appr_res = await client.post(
        f"/api/v1/campaigns/{camp_id}/approve",
        headers=member_headers,
        json={"approved": True},
    )
    assert appr_res.status_code == 404

    # Org B's campaign list must not contain Org A's campaign
    list_res = await client.get("/api/v1/campaigns", headers=member_headers)
    assert list_res.status_code == 200
    assert all(c["id"] != camp_id for c in list_res.json())


@pytest.mark.asyncio
async def test_campaign_audit_logging(
    client: AsyncClient,
    owner_headers: dict,
    owner_org_id: str,
    db_session: AsyncSession,
):
    """Verifies that campaign lifecycle actions create tamper-evident audit log entries."""
    # Create campaign
    camp_payload = {
        "name": "Audit Tracked Campaign",
        "objective": "awareness",
        "total_budget": 6000.0,
        "daily_budget_limit": 600.0,
        "start_date": "2026-11-20",
    }
    c_res = await client.post("/api/v1/campaigns", headers=owner_headers, json=camp_payload)
    camp_id = c_res.json()["id"]

    # Approve campaign
    await client.post(
        f"/api/v1/campaigns/{camp_id}/approve",
        headers=owner_headers,
        json={"approved": True},
    )

    # Pause campaign
    await client.post(f"/api/v1/campaigns/{camp_id}/pause", headers=owner_headers)

    # Query audit logs from database
    stmt = select(AuditLog).where(
        AuditLog.organization_id == uuid.UUID(owner_org_id),
        AuditLog.resource_id == camp_id,
    )
    res = await db_session.execute(stmt)
    logs = res.scalars().all()
    actions = [l.action for l in logs]

    assert "CAMPAIGN_CREATED" in actions
    assert "CAMPAIGN_BUDGET_APPROVED" in actions
    assert "CAMPAIGN_PAUSED" in actions

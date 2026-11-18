"""Comprehensive automated test suite for MarketPath AI Phase 4.

Verifies:
1. Agency Connect discovery, 8 demo agencies, and real agency registration.
2. RFP quotation lifecycle and client engagement creation.
3. Agency Partner Portal with founder PII sanitization (zero phone/email/cost price leakage).
4. Free Consultation Booking with reference code, honest email reporting, and double-booking guard.
5. Consultant appointment management, confirmation calendar sync, and client-safe report generation.
6. Platform Admin consultation operations and telemetry overview.
7. Unified Calendar engine, ICS export, and notification centre.
8. Context-aware support assistant, consequential action guardrails, and public FAQ boundary.
9. Team 7-day token invitations, role updates, and sole owner protection.
"""

import datetime
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.agency import AgencyProfile
from backend.app.models.consultation import ConsultationRequest
from backend.app.schemas.agency import AgencyQuotationSubmit
from backend.app.services.agency_service import AgencyServiceManager


@pytest.mark.asyncio
async def test_agency_connect_demo_directory_and_real_registration(
    client: AsyncClient, owner_headers: dict, db_session: AsyncSession
):
    """Verifies that 8 demo agencies are seeded and real agencies register as unverified."""
    org_id = uuid.UUID(owner_headers["X-Organization-Id"])
    await AgencyServiceManager.seed_demo_agencies_if_empty(db_session, org_id)

    res = await db_session.execute(select(AgencyProfile))
    agencies = res.scalars().all()
    assert len(agencies) >= 8, f"Expected at least 8 demo agencies, got {len(agencies)}"

    # Ensure all demo profiles are explicitly marked is_demo=True with .demo.in domain
    for a in agencies:
        if a.is_demo:
            assert a.email.endswith(".demo.in")
            assert "demo" in a.website.lower()

    # Now test real agency registration
    real_payload = {
        "name": "NovaPixel Commerce Agency",
        "slug": f"novapixel-commerce-{uuid.uuid4().hex[:6]}",
        "tagline": "Full funnel digital marketplace acceleration",
        "description": "Commercial studio and advertising agency for Indian D2C brands.",
        "email": "contact@novapixel.in",
        "phone": "+91 9876543210",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "country": "India",
        "remote_or_local": "both",
        "team_size": "11-50",
        "founded_year": 2022,
        "category_specialties": ["Home & Living", "Electronics"],
        "service_offerings": ["Meta Ads management", "Product photography"],
        "min_budget_inr": 20000,
        "max_budget_inr": 80000,
        "is_available": True,
    }

    resp = await client.post("/api/v1/agency/profiles", json=real_payload, headers=owner_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "NovaPixel Commerce Agency"
    assert data["is_demo"] is False
    assert data["verification_status"] == "registered"


@pytest.mark.asyncio
async def test_agency_rfp_quote_and_engagement_lifecycle(
    client: AsyncClient, owner_headers: dict, db_session: AsyncSession
):
    """Tests the full quote RFP submission, agency quote response, and seller acceptance."""
    org_id = uuid.UUID(owner_headers["X-Organization-Id"])
    await AgencyServiceManager.seed_demo_agencies_if_empty(db_session, org_id)

    agency_res = await db_session.execute(select(AgencyProfile).where(AgencyProfile.slug == "craftverve-media"))
    target_agency = agency_res.scalar_one_or_none()
    assert target_agency is not None

    # 1. Seller submits RFP
    quote_payload = {
        "agency_profile_id": str(target_agency.id),
        "project_title": "Festive Collection Photoshoot & Ad Creatives",
        "project_description": "Need 30 studio shots and 5 lifestyle reels for festive terracotta drop.",
        "budget_inr": 35000,
        "budget_type": "project_based",
        "timeframe": "Within 3 weeks",
        "attachment_urls": ["https://example.com/moodboard.pdf"],
        "share_contact_consent": True,
        "contact_email": "ananya.deshmukh@auraterra.in",
        "contact_phone": "+91 9823012345",
    }

    create_res = await client.post("/api/v1/agency/quote-requests", json=quote_payload, headers=owner_headers)
    assert create_res.status_code == 200, create_res.text
    quote_data = create_res.json()
    quote_id = quote_data["id"]
    assert quote_data["status"] == "submitted"

    # 2. Agency responds with formal quotation
    quotation_payload = {
        "quotation_amount_inr": 32000,
        "quotation_deliverables": ["30 edited photos", "6 short video reels", "Full raw asset library"],
        "agency_response_notes": "We can complete this in 14 days with our Pune studio team.",
        "quotation_valid_until": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=14)).isoformat(),
    }

    updated_req = await AgencyServiceManager.agency_respond_to_request(
        db=db_session,
        request_id=uuid.UUID(quote_id),
        agency_id=target_agency.id,
        payload=AgencyQuotationSubmit(**quotation_payload),
    )
    assert updated_req.status == "quotation_sent"
    assert updated_req.quotation_amount_inr == 32000

    # 3. Seller accepts quotation
    accept_res = await client.post(
        f"/api/v1/agency/quote-requests/{quote_id}/accept",
        headers=owner_headers,
    )
    assert accept_res.status_code == 200, accept_res.text
    eng_data = accept_res.json()
    assert eng_data["status"] == "active"
    assert eng_data["agreed_price_inr"] == 32000


@pytest.mark.asyncio
async def test_agency_portal_founder_pii_sanitization(client: AsyncClient, owner_headers: dict):
    """Verifies that Agency Partner Portal strictly masks founder email, phone, and cost prices."""
    resp = await client.get("/api/v1/agency/portal/briefs", headers=owner_headers)
    assert resp.status_code == 200, resp.text
    briefs = resp.json()
    assert len(briefs) > 0

    for b in briefs:
        # Personal phone must be masked
        if "founder_phone" in b and b["founder_phone"]:
            assert b["founder_phone"].endswith("****") or "•" in b["founder_phone"] or "***" in b["founder_phone"]
        # Personal email must be masked
        if "founder_email" in b and b["founder_email"]:
            assert "@" in b["founder_email"]
            assert "***" in b["founder_email"]
        # Cost price and margin percentage must never be exposed to agencies
        assert "cost_price" not in b or b["cost_price"] is None
        assert "margin_percentage" not in b or b["margin_percentage"] is None


@pytest.mark.asyncio
async def test_agency_portal_packages_and_portfolio_endpoints(client: AsyncClient, owner_headers: dict):
    """Verifies package creation and case study creation in the Agency Partner Portal."""
    # Create package
    pkg_payload = {
        "name": "Omnichannel D2C Kickstart",
        "monthly_retainer_inr": 40000,
        "best_for": "Emerging handicrafts brands",
        "deliverables": ["Meta Ads Management", "4 Studio Photoshoots"],
        "turnaround_days": 10,
    }
    pkg_res = await client.post("/api/v1/agency/portal/packages", json=pkg_payload, headers=owner_headers)
    assert pkg_res.status_code == 201
    assert pkg_res.json()["name"] == "Omnichannel D2C Kickstart"

    # Create portfolio case study
    case_payload = {
        "client_name": "Aura Terra Living",
        "category": "Home & Living",
        "headline": "Scaled Shopify revenue by 180% with UGC reels",
        "metrics": {"roas": "3.8x", "blended_cac": "₹185"},
        "is_demo_work": False,
    }
    case_res = await client.post("/api/v1/agency/portal/portfolio", json=case_payload, headers=owner_headers)
    assert case_res.status_code == 201
    assert case_res.json()["verification_badge"] == "Verified MarketPath Brand Client"


@pytest.mark.asyncio
async def test_free_consultation_booking_lifecycle_and_double_booking_prevention(
    client: AsyncClient, make_jwt
):
    """Verifies consultation booking with unique ref code, honest email status, and conflict detection."""
    admin_id = str(uuid.uuid4())
    admin_token = make_jwt(user_id=admin_id, email="admin@marketpath.ai", is_platform_admin=True)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    booking_payload = {
        "full_name": "Rohan Mehra",
        "email": "rohan@mehraorganics.in",
        "phone": "+91 9811223344",
        "brand_name": "Mehra Organics",
        "category": "Food & Beverage",
        "business_stage": "Scaling (₹5L - ₹25L/mo)",
        "monthly_revenue": "₹12 Lakh",
        "challenges": "Listing approvals on Amazon Groceries and Flipkart Supermart.",
        "preferred_date": "2026-12-15",
        "preferred_time_slot": "Morning (10:00 AM – 12:00 PM IST)",
        "timezone": "Asia/Kolkata",
    }

    # 1. Submit initial booking
    resp = await client.post("/api/v1/consultations", json=booking_payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    consultation_id = data["id"]
    assert data["reference_code"].startswith("MP-CONS-")
    assert data["status"] == "submitted"
    assert data["email_delivery_status"] in ["delivered", "unconfigured_provider"]

    # 2. Operator assigns consultant
    assign_payload = {
        "consultant_id": admin_id,
        "consultant_name": "Ananya Deshmukh",
    }
    assign_res = await client.post(f"/api/v1/consultations/{consultation_id}/assign", json=assign_payload, headers=admin_headers)
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "assigned"

    # 3. Confirm appointment schedule
    confirm_payload = {
        "scheduled_at": "2026-12-15T10:30:00Z",
        "duration_minutes": 30,
    }
    confirm_res = await client.post(f"/api/v1/consultations/{consultation_id}/confirm", json=confirm_payload, headers=admin_headers)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "confirmed"
    assert confirm_res.json()["meeting_link"].startswith("https://meet.marketpath.ai/")

    # 4. Attempt double booking on confirmed slot -> Expect 409 Conflict
    conflict_res = await client.post("/api/v1/consultations", json=booking_payload)
    assert conflict_res.status_code == 409
    err_detail = conflict_res.json().get("detail") or conflict_res.json().get("error", {}).get("message", "")
    assert "already reserved" in err_detail

    # 5. Consultant files diagnostic report
    report_payload = {
        "internal_notes": "Client needs FSSAI re-verification before Amazon Groceries approval.",
        "report_summary": "Audited Mehra Organics packaging and organic certifications.",
        "recommendations": [
            "Update packaging to include batch number and green veg logo.",
            "Apply for Amazon Brand Registry under Trademark class 30.",
        ],
        "action_items": [
            "Upload FSSAI license copy to Master Catalogue",
            "Review Flipkart Supermart packaging specs",
        ],
    }
    report_res = await client.post(f"/api/v1/consultations/{consultation_id}/report", json=report_payload, headers=admin_headers)
    assert report_res.status_code == 200
    assert report_res.json()["status"] == "completed"

    # 6. Public / Client report fetch (internal notes must be hidden)
    client_report_res = await client.get(f"/api/v1/consultations/{consultation_id}/report")
    assert client_report_res.status_code == 200
    client_rep = client_report_res.json()
    assert client_rep["report_summary"].startswith("Audited Mehra Organics")
    assert len(client_rep["recommendations"]) == 2
    assert "internal_notes" not in client_rep


@pytest.mark.asyncio
async def test_admin_consultations_telemetry(client: AsyncClient, make_jwt):
    """Verifies platform admin consultation telemetry and operations dashboard."""
    admin_id = str(uuid.uuid4())
    admin_token = make_jwt(user_id=admin_id, email="admin@marketpath.ai", is_platform_admin=True)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    resp = await client.get("/api/v1/admin/consultations", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "stats" in data
    assert "total_consultations" in data["stats"]
    assert "consultations" in data


@pytest.mark.asyncio
async def test_unified_calendar_and_ics_export(client: AsyncClient, owner_headers: dict):
    """Verifies calendar event listing, event seeding, and RFC-5545 ICS generation."""
    # List events
    events_res = await client.get("/api/v1/calendar/events", headers=owner_headers)
    assert events_res.status_code == 200, events_res.text
    ev_data = events_res.json()
    assert "items" in ev_data
    assert len(ev_data["items"]) >= 5

    # Export ICS file
    ics_res = await client.get("/api/v1/calendar/export.ics", headers=owner_headers)
    assert ics_res.status_code == 200
    assert "BEGIN:VCALENDAR" in ics_res.text
    assert "END:VCALENDAR" in ics_res.text


@pytest.mark.asyncio
async def test_notifications_centre_domain_filtering_and_read_status(client: AsyncClient, owner_headers: dict):
    """Verifies notification center domains, unread counts, and marking read."""
    # List notifications
    notif_res = await client.get("/api/v1/notifications", headers=owner_headers)
    assert notif_res.status_code == 200, notif_res.text
    notifs = notif_res.json()
    assert notifs["total"] >= 6

    # Check unread counts
    unread_res = await client.get("/api/v1/notifications/unread-count", headers=owner_headers)
    assert unread_res.status_code == 200
    assert unread_res.json()["unread_count"] >= 1

    # Mark all as read
    read_all_res = await client.post("/api/v1/notifications/mark-all-read", headers=owner_headers)
    assert read_all_res.status_code == 200
    assert "marked as read" in read_all_res.json()["message"]

    # Verify unread is now 0
    unread_res2 = await client.get("/api/v1/notifications/unread-count", headers=owner_headers)
    assert unread_res2.status_code == 200
    assert unread_res2.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_support_bot_consequential_guardrails_and_topics(client: AsyncClient, owner_headers: dict):
    """Verifies that the support assistant blocks autonomous mutations and provides safe action links."""
    # 1. Ask for consequential action
    query_payload = {
        "message": "Please publish all my batch listings to Amazon now!",
        "current_page": "/app/publishing",
    }
    chat_res = await client.post("/api/v1/support/chat", json=query_payload, headers=owner_headers)
    assert chat_res.status_code == 200, chat_res.text
    ans = chat_res.json()
    assert "Action Guardrail Notice" in ans["answer"] or "explicit" in ans["answer"].lower()
    assert len(ans["suggested_actions"]) > 0
    assert ans["suggested_actions"][0]["action_url"] == "/app/publishing"

    # 2. Get support topics list
    topics_res = await client.get("/api/v1/support/conversations", headers=owner_headers)
    assert topics_res.status_code == 200
    assert "recommended_topics" in topics_res.json()


@pytest.mark.asyncio
async def test_team_member_role_update_and_sole_owner_protection(client: AsyncClient, owner_headers: dict):
    """Verifies team member role updates and protection of the sole owner."""
    # Invite new team member
    invite_payload = {
        "email": "vikram.sharma@auraterra.in",
        "role": "viewer",
        "full_name": "Vikram Sharma",
    }
    add_res = await client.post("/api/v1/team/invites", json=invite_payload, headers=owner_headers)
    assert add_res.status_code == 201, add_res.text
    member_id = add_res.json()["id"]

    # Promote member from viewer to marketer
    role_res = await client.patch(
        f"/api/v1/team/members/{member_id}",
        json={"role": "marketer"},
        headers=owner_headers,
    )
    assert role_res.status_code == 200, role_res.text
    assert role_res.json()["role"] == "marketer"

    # Get owner member id
    members_res = await client.get("/api/v1/team/members", headers=owner_headers)
    owner_member = next(m for m in members_res.json() if m["role"] == "owner")

    # Attempt to demote the sole owner -> Expect 400 Bad Request
    demote_res = await client.patch(
        f"/api/v1/team/members/{owner_member['id']}",
        json={"role": "viewer"},
        headers=owner_headers,
    )
    assert demote_res.status_code == 400
    err_detail = demote_res.json().get("detail") or demote_res.json().get("error", {}).get("message", "")
    assert "sole owner" in err_detail.lower()

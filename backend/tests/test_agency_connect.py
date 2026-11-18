import datetime
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.agency import (
    AgencyEngagement,
    AgencyPortfolio,
    AgencyProfile,
    AgencyQuoteRequest,
    AgencyReview,
    AgencySavedShortlist,
    AgencyService,
    AgencyServicePackage,
    SellerAgencyRequirement,
)
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import UserProfile
from backend.app.schemas.agency import AgencyQuotationSubmit
from backend.app.services.agency_matching_service import AgencyMatchingEngine
from backend.app.services.agency_service import AgencyServiceManager


@pytest.mark.asyncio
async def test_agency_registration_and_admin_verification(
    client: AsyncClient, owner_headers: dict, db_session: AsyncSession, make_jwt
):
    """Verifies that an agency registers with 'registered' status and only a Platform Admin can verify."""
    # 1. Register new agency profile
    reg_payload = {
        "name": "Zenith Growth Labs",
        "slug": "zenith-growth-labs",
        "tagline": "D2C Meta Ads & Creative Engine",
        "description": "Zenith provides full-funnel digital marketing and photoshoots.",
        "email": "contact@zenith.in",
        "city": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "remote_or_local": "both",
        "team_size": "1-10",
        "founded_year": 2022,
        "category_specialties": ["Home & Living", "Handicrafts & Decor"],
        "service_offerings": ["Product photography", "Meta Ads management", "Social media management"],
        "min_budget_inr": 12000,
        "gst_number": "27AAACZ1111F1Z1",
        "is_available": True,
    }

    res = await client.post("/api/v1/agency/profiles", json=reg_payload, headers=owner_headers)
    assert res.status_code == 200, res.text
    agency_data = res.json()
    agency_id = agency_data["id"]

    # Verify status is strictly 'registered'
    assert agency_data["verification_status"] == "registered"
    assert agency_data["verified_at"] is None

    # 2. Ordinary seller tries to approve -> must fail 403
    patch_payload = {
        "verification_status": "verified",
        "verification_notes": "Official GST verified",
    }
    fail_res = await client.patch(
        f"/api/v1/admin/agencies/{agency_id}/verification",
        json=patch_payload,
        headers=owner_headers,
    )
    assert fail_res.status_code == 403

    # 3. Platform Admin verifies agency
    admin_user = UserProfile(
        id=uuid.uuid4(),
        email="superadmin@marketpath.ai",
        full_name="Super Admin",
        is_platform_admin=True,
    )
    db_session.add(admin_user)
    await db_session.commit()

    admin_token = make_jwt(str(admin_user.id), admin_user.email, is_platform_admin=True)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    verify_res = await client.patch(
        f"/api/v1/admin/agencies/{agency_id}/verification",
        json=patch_payload,
        headers=admin_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_status"] == "verified"


@pytest.mark.asyncio
async def test_seller_requirement_ai_extraction_and_storage(
    client: AsyncClient, owner_headers: dict, db_session: AsyncSession
):
    """Tests AI requirement parsing and saving active seller business briefs."""
    extract_payload = {
        "brand_name": "Aura Terra Living",
        "product_category": "Home Decor",
        "business_stage": "Early Stage",
        "location": "Pune",
        "selected_objectives": ["Increase online sales", "Improve social media presence"],
        "selected_services": ["Product photography", "Meta Ads management"],
        "monthly_budget_inr": 15000,
        "raw_brief_text": "We make handmade ceramic planters and vases. Looking for local or remote agency to shoot photos and run Instagram ads.",
    }

    ai_res = await client.post("/api/v1/agency/requirements/ai-extract", json=extract_payload, headers=owner_headers)
    assert ai_res.status_code == 200, ai_res.text
    ai_data = ai_res.json()
    assert "search_brief" in ai_data
    assert len(ai_data["identified_services"]) == 2
    assert "budget_advisory" in ai_data

    # Save requirement
    save_payload = {
        **extract_payload,
        "ai_search_brief": ai_data["search_brief"],
        "ai_suggested_services": ai_data["suggested_additional_services"],
    }
    save_res = await client.post("/api/v1/agency/requirements", json=save_payload, headers=owner_headers)
    assert save_res.status_code == 200
    saved_data = save_res.json()
    assert saved_data["brand_name"] == "Aura Terra Living"
    assert saved_data["monthly_budget_inr"] == 15000

    # Fetch active
    active_res = await client.get("/api/v1/agency/requirements/active", headers=owner_headers)
    assert active_res.status_code == 200
    assert active_res.json()["id"] == saved_data["id"]


@pytest.mark.asyncio
async def test_agency_matching_engine_and_explanations(
    client: AsyncClient, owner_headers: dict, db_session: AsyncSession
):
    """Verifies that the matching engine applies hard eligibility filters, weighted scoring, and transparent explanations."""
    org_id = uuid.UUID(owner_headers["X-Organization-Id"])
    await AgencyServiceManager.seed_demo_agencies_if_empty(db_session, org_id)

    # Request recommendations for active requirement
    rec_res = await client.get("/api/v1/agency/recommendations", headers=owner_headers)
    assert rec_res.status_code == 200, rec_res.text
    rec_data = rec_res.json()

    assert rec_data["total_eligible"] >= 1
    matches = rec_data["matches"]
    top_match = matches[0]

    # Verify transparent explanation structure
    explanation = top_match["explanation"]
    assert "why_matched" in explanation
    assert "budget_compatibility_note" in explanation
    assert "location_compatibility_note" in explanation
    assert "score_breakdown" in explanation
    assert 0 <= top_match["match_score"] <= 100

    # Organic score ordering: top match score >= subsequent match score
    if len(matches) > 1:
        assert matches[0]["match_score"] >= matches[1]["match_score"]


@pytest.mark.asyncio
async def test_agency_discovery_and_filtering(
    client: AsyncClient, owner_headers: dict, db_session: AsyncSession
):
    """Verifies multi-faceted search across city, service, and budget thresholds."""
    org_id = uuid.UUID(owner_headers["X-Organization-Id"])
    await AgencyServiceManager.seed_demo_agencies_if_empty(db_session, org_id)

    # 1. Search Pune
    res_pune = await client.get("/api/v1/agency/discover?location=Pune")
    assert res_pune.status_code == 200
    pune_agencies = res_pune.json()
    assert any(a["city"] == "Pune" for a in pune_agencies)

    # 2. Budget filter (max budget ₹14,000 should include ₹12,000 agency, exclude ₹25,000 agency)
    res_budget = await client.get("/api/v1/agency/discover?max_budget=14000")
    assert res_budget.status_code == 200
    for a in res_budget.json():
        assert a["min_budget_inr"] <= 14000

    # 3. Profile details by slug
    slug = pune_agencies[0]["slug"]
    res_detail = await client.get(f"/api/v1/agency/profiles/{slug}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["slug"] == slug
    assert "packages" in detail
    assert "portfolios" in detail


@pytest.mark.asyncio
async def test_quote_request_quotation_and_engagement_lifecycle(
    client: AsyncClient, owner_headers: dict, db_session: AsyncSession
):
    """Tests the complete proposal, quotation, and engagement lifecycle between seller and agency."""
    org_id = uuid.UUID(owner_headers["X-Organization-Id"])
    await AgencyServiceManager.seed_demo_agencies_if_empty(db_session, org_id)

    # 1. Find target agency
    ag_res = await db_session.execute(select(AgencyProfile).where(AgencyProfile.slug == "craftverve-media"))
    agency = ag_res.scalar_one_or_none()
    assert agency is not None

    # 2. Seller submits quote request
    quote_payload = {
        "agency_profile_id": str(agency.id),
        "project_title": "Summer Home Decor Campaign",
        "project_description": "We need 20 photos and 4 reels for our new ceramic planter line.",
        "budget_inr": 15000,
        "budget_type": "monthly",
        "timeframe": "1 Month",
        "attachment_urls": ["https://marketpath.ai/demo-brief.pdf"],
        "share_contact_consent": True,
        "contact_email": "seller@auraterra.in",
        "contact_phone": "+91 98765 43210",
    }

    sub_res = await client.post("/api/v1/agency/quote-requests", json=quote_payload, headers=owner_headers)
    assert sub_res.status_code == 200, sub_res.text
    req_data = sub_res.json()
    req_id = req_data["id"]
    assert req_data["status"] == "submitted"

    # 3. Seller views quote requests list
    list_res = await client.get("/api/v1/agency/quote-requests", headers=owner_headers)
    assert list_res.status_code == 200
    assert any(r["id"] == req_id for r in list_res.json())

    # 4. Agency prepares formal quotation
    quotation_payload = {
        "quotation_amount_inr": 15000,
        "quotation_deliverables": [
            "20 Edited Studio Product Images",
            "4 Short-form Instagram Reels",
            "Meta Ads Audience Setup",
        ],
        "agency_response_notes": "We would love to collaborate on your ceramic collection. Ready to start next week.",
    }

    # Agency responds
    updated_req = await AgencyServiceManager.agency_respond_to_request(
        db=db_session,
        request_id=uuid.UUID(req_id),
        agency_id=agency.id,
        payload=AgencyQuotationSubmit(**quotation_payload),
    )
    assert updated_req.status == "quotation_sent"
    assert updated_req.quotation_amount_inr == 15000

    # 5. Seller accepts quotation -> establishes active engagement
    accept_res = await client.post(f"/api/v1/agency/quote-requests/{req_id}/accept", headers=owner_headers)
    assert accept_res.status_code == 200, accept_res.text
    engagement_data = accept_res.json()
    engagement_id = engagement_data["id"]
    assert engagement_data["status"] == "active"
    assert engagement_data["agreed_price_inr"] == 15000

    # 6. Seller posts verified review after engagement
    review_payload = {
        "engagement_id": engagement_id,
        "rating": 5,
        "title": "Outstanding Product Photography & Reels",
        "review_text": "CraftVerve delivered warm, stunning studio shots that significantly improved our conversion rates.",
    }
    rev_res = await client.post(
        f"/api/v1/agency/engagements/{engagement_id}/review",
        json=review_payload,
        headers=owner_headers,
    )
    assert rev_res.status_code == 200, rev_res.text
    review_data = rev_res.json()
    assert review_data["is_verified"] is True
    assert review_data["rating"] == 5

    # 7. Check agency reviews
    ag_rev_res = await client.get(f"/api/v1/agency/profiles/{agency.id}/reviews")
    assert ag_rev_res.status_code == 200
    assert len(ag_rev_res.json()) >= 1


@pytest.mark.asyncio
async def test_agency_saved_shortlists(
    client: AsyncClient, owner_headers: dict, db_session: AsyncSession
):
    """Tests saving, unsaving, and retrieving bookmarked agencies."""
    org_id = uuid.UUID(owner_headers["X-Organization-Id"])
    await AgencyServiceManager.seed_demo_agencies_if_empty(db_session, org_id)

    ag_res = await db_session.execute(select(AgencyProfile).limit(1))
    agency = ag_res.scalars().first()
    assert agency is not None

    # Toggle save
    save_res = await client.post(f"/api/v1/agency/shortlists/{agency.id}", headers=owner_headers)
    assert save_res.status_code == 200
    assert save_res.json()["saved"] is True

    # List saved
    list_saved = await client.get("/api/v1/agency/shortlists", headers=owner_headers)
    assert list_saved.status_code == 200
    saved_agencies = list_saved.json()
    assert any(a["id"] == str(agency.id) for a in saved_agencies)

    # Toggle unsave
    unsave_res = await client.post(f"/api/v1/agency/shortlists/{agency.id}", headers=owner_headers)
    assert unsave_res.status_code == 200
    assert unsave_res.json()["saved"] is False

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, get_current_tenant_context, get_current_user
from backend.app.core.sanitizer import mask_email, mask_phone, sanitize_client_brief
from backend.app.models.agency import SellerAgencyRequirement
from backend.app.models.organization import Organization
from backend.app.models.user import UserProfile
from backend.app.schemas.agency import (
    AIRequirementExtractionRequest,
    AIRequirementExtractionResponse,
    AgencyEngagementRead,
    AgencyMatchCard,
    AgencyProfileCreate,
    AgencyProfileDetailRead,
    AgencyProfileRead,
    AgencyQuotationSubmit,
    AgencyQuoteRequestCreate,
    AgencyQuoteRequestRead,
    AgencyRecommendationResponse,
    AgencyReviewCreate,
    AgencyReviewRead,
    SellerRequirementCreate,
    SellerRequirementRead,
)
from backend.app.services.agency_ai_service import AgencyAIService
from backend.app.services.agency_matching_service import AgencyMatchingEngine
from backend.app.services.agency_service import AgencyServiceManager

router = APIRouter(prefix="/agency", tags=["MarketPath Agency Connect"])


# -----------------------------------------------------------------------------
# 1. AI Requirement Extraction & Onboarding Wizard
# -----------------------------------------------------------------------------

@router.post("/requirements/ai-extract", response_model=AIRequirementExtractionResponse)
async def extract_ai_requirements(
    payload: AIRequirementExtractionRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """Uses Gemini to parse seller inputs, identify missing information, and formulate an agency search brief."""
    return await AgencyAIService.extract_and_structure_requirements(payload)


@router.post("/requirements", response_model=SellerRequirementRead)
async def save_seller_requirement(
    payload: SellerRequirementCreate,
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Saves or updates the seller's active business requirement profile."""
    return await AgencyServiceManager.create_or_update_seller_requirement(
        db, tenant_ctx.organization_id, payload
    )


@router.get("/requirements/active", response_model=Optional[SellerRequirementRead])
async def get_active_seller_requirement(
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Fetches the seller's most recent active requirement profile."""
    return await AgencyServiceManager.get_seller_requirement(db, tenant_ctx.organization_id)


# -----------------------------------------------------------------------------
# 2. Agency Discovery & Recommendations Engine
# -----------------------------------------------------------------------------

@router.get("/discover", response_model=List[AgencyProfileRead])
async def discover_agencies(
    search: Optional[str] = Query(None, description="Search keyword"),
    category: Optional[str] = Query(None, description="Filter by product category specialty"),
    service: Optional[str] = Query(None, description="Filter by specific service capability"),
    location: Optional[str] = Query(None, description="Filter by city or state"),
    max_budget: Optional[int] = Query(None, description="Maximum starting budget in INR"),
    remote_only: bool = Query(False, description="Filter for remote-capable agencies"),
    verification_status: Optional[str] = Query(None, description="Filter by verification standing"),
    db: AsyncSession = Depends(get_db),
):
    """Discovers agencies using multifaceted search and deterministic filters."""
    return await AgencyServiceManager.list_agencies_for_discovery(
        db=db,
        search=search,
        category=category,
        service=service,
        location=location,
        max_budget=max_budget,
        remote_only=remote_only,
        verification_status=verification_status,
    )


@router.get("/recommendations", response_model=AgencyRecommendationResponse)
async def get_agency_recommendations(
    requirement_id: Optional[uuid.UUID] = Query(None, description="Specific requirement ID to match against"),
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Generates transparent, explainable agency matches using hard eligibility filters and weighted ranking."""
    req = None
    if requirement_id:
        req = await db.get(SellerAgencyRequirement, requirement_id)
    else:
        req_read = await AgencyServiceManager.get_seller_requirement(db, tenant_ctx.organization_id)
        if req_read:
            req = await db.get(SellerAgencyRequirement, req_read.id)

    if not req:
        # If seller has no saved requirements yet, build a dynamic fallback requirement from organization profile
        req = SellerAgencyRequirement(
            organization_id=tenant_ctx.organization_id,
            brand_name=tenant_ctx.organization.name,
            product_category="General Merchandise",
            business_stage="Scaling",
            location="India",
            required_services=["Digital marketing", "Product photography", "Meta Ads management"],
            monthly_budget_inr=20000,
            remote_or_local="both",
            is_active=True,
        )

    return await AgencyMatchingEngine.match_agencies_for_requirement(
        db=db, requirement=req, include_demo=True
    )


@router.get("/profiles/{slug}", response_model=AgencyProfileDetailRead)
async def get_agency_profile_detail(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves an agency's comprehensive public profile, including services, packages, and portfolios."""
    agency = await AgencyServiceManager.get_agency_by_slug(db, slug)
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency profile not found.")
    return agency


@router.post("/profiles", response_model=AgencyProfileRead)
async def register_agency_profile(
    payload: AgencyProfileCreate,
    current_user: UserProfile = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Registers an agency profile under the current organization tenant. Status defaults to 'registered'."""
    return await AgencyServiceManager.register_agency_profile(
        db=db, org_id=tenant_ctx.organization_id, payload=payload, user_id=current_user.id
    )


# -----------------------------------------------------------------------------
# 3. Shortlists & Saved Agencies
# -----------------------------------------------------------------------------

@router.post("/shortlists/{agency_id}")
async def toggle_save_agency_bookmark(
    agency_id: uuid.UUID,
    notes: Optional[str] = Query(None),
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Saves or removes an agency from the seller's shortlisted comparison list."""
    is_saved = await AgencyServiceManager.toggle_save_agency(db, tenant_ctx.organization_id, agency_id, notes)
    return {"saved": is_saved, "agency_id": str(agency_id)}


@router.get("/shortlists", response_model=List[AgencyProfileRead])
async def list_saved_agencies(
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Lists all shortlisted agencies bookmarked by the seller organization."""
    return await AgencyServiceManager.list_saved_agencies(db, tenant_ctx.organization_id)


# -----------------------------------------------------------------------------
# 4. Quotations & Introductions Workflow
# -----------------------------------------------------------------------------

@router.post("/quote-requests", response_model=AgencyQuoteRequestRead)
async def submit_quote_request(
    payload: AgencyQuoteRequestCreate,
    current_user: UserProfile = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Seller submits a structured RFP or quotation request to an agency."""
    return await AgencyServiceManager.submit_quote_request(
        db=db, org_id=tenant_ctx.organization_id, payload=payload, user_id=current_user.id
    )


@router.get("/quote-requests", response_model=List[AgencyQuoteRequestRead])
async def list_seller_quote_requests(
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Seller views all outgoing quote requests and their real-time statuses."""
    return await AgencyServiceManager.list_seller_quote_requests(db, tenant_ctx.organization_id)


@router.get("/agency-portal/requests", response_model=List[AgencyQuoteRequestRead])
async def list_agency_inbound_requests(
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Agency views inbound RFPs submitted by prospective D2C clients."""
    from backend.app.models.agency import AgencyProfile
    from sqlalchemy import select
    res = await db.execute(select(AgencyProfile).where(AgencyProfile.organization_id == tenant_ctx.organization_id))
    agency = res.scalar_one_or_none()
    if not agency:
        return []
    return await AgencyServiceManager.list_agency_inbound_requests(db, agency.id)


@router.post("/agency-portal/requests/{request_id}/respond", response_model=AgencyQuoteRequestRead)
async def agency_respond_quotation(
    request_id: uuid.UUID,
    payload: AgencyQuotationSubmit,
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Agency responds with a formal proposal, deliverables breakdown, and price quotation."""
    from backend.app.models.agency import AgencyProfile
    from sqlalchemy import select
    res = await db.execute(select(AgencyProfile).where(AgencyProfile.organization_id == tenant_ctx.organization_id))
    agency = res.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No registered agency profile found for this tenant.")

    try:
        return await AgencyServiceManager.agency_respond_to_request(
            db=db, request_id=request_id, agency_id=agency.id, payload=payload
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/quote-requests/{request_id}/accept", response_model=AgencyEngagementRead)
async def seller_accept_quotation(
    request_id: uuid.UUID,
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Seller accepts the agency's quotation, transitioning the RFP into an active engagement."""
    try:
        return await AgencyServiceManager.seller_accept_quotation(
            db=db, request_id=request_id, org_id=tenant_ctx.organization_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/engagements", response_model=List[AgencyEngagementRead])
async def list_active_engagements(
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Lists all active and completed engagements for this seller tenant."""
    from backend.app.models.agency import AgencyEngagement, AgencyProfile
    from sqlalchemy import select
    stmt = (
        select(AgencyEngagement, AgencyProfile.name.label("agency_name"))
        .join(AgencyProfile, AgencyEngagement.agency_profile_id == AgencyProfile.id)
        .where(AgencyEngagement.organization_id == tenant_ctx.organization_id)
        .order_by(AgencyEngagement.created_at.desc())
    )
    res = await db.execute(stmt)
    results = []
    for eng, ag_name in res.all():
        eng_read = AgencyEngagementRead.model_validate(eng)
        eng_read.agency_name = ag_name
        results.append(eng_read)
    return results


# -----------------------------------------------------------------------------
# 5. Verified Reviews & Feedback
# -----------------------------------------------------------------------------

@router.post("/engagements/{engagement_id}/review", response_model=AgencyReviewRead)
async def submit_verified_review(
    engagement_id: uuid.UUID,
    payload: AgencyReviewCreate,
    tenant_ctx: TenantContext = Depends(get_current_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Submits a verified review following a contracted engagement (never fake or unverified)."""
    from backend.app.models.agency import AgencyEngagement, AgencyReview
    from sqlalchemy import select
    eng = await db.get(AgencyEngagement, engagement_id)
    if not eng or eng.organization_id != tenant_ctx.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found or unauthorized.")

    existing = await db.execute(select(AgencyReview).where(AgencyReview.engagement_id == engagement_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A review has already been submitted for this engagement.")

    review = AgencyReview(
        engagement_id=engagement_id,
        organization_id=tenant_ctx.organization_id,
        agency_profile_id=eng.agency_profile_id,
        rating=payload.rating,
        title=payload.title,
        review_text=payload.review_text,
        is_verified=True,
    )
    db.add(review)

    # Recalculate agency average rating
    from backend.app.models.agency import AgencyProfile
    from sqlalchemy import func
    agency = await db.get(AgencyProfile, eng.agency_profile_id)
    if agency:
        agency.reviews_count += 1
        avg_res = await db.execute(
            select(func.avg(AgencyReview.rating)).where(AgencyReview.agency_profile_id == agency.id)
        )
        agency.rating_avg = round(float(avg_res.scalar() or payload.rating), 2)

    await db.commit()
    await db.refresh(review)
    return AgencyReviewRead.model_validate(review)


@router.get("/profiles/{agency_id}/reviews", response_model=List[AgencyReviewRead])
async def list_agency_verified_reviews(
    agency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Lists all verified reviews submitted by real D2C sellers for this agency."""
    from backend.app.models.agency import AgencyReview
    from sqlalchemy import select
    stmt = (
        select(AgencyReview, Organization.name.label("reviewer_org_name"))
        .join(Organization, AgencyReview.organization_id == Organization.id)
        .where(AgencyReview.agency_profile_id == agency_id)
        .order_by(AgencyReview.created_at.desc())
    )
    res = await db.execute(stmt)
    results = []
    for r, org_name in res.all():
        r_read = AgencyReviewRead.model_validate(r)
        r_read.reviewer_org_name = org_name
        results.append(r_read)
    return results


# -----------------------------------------------------------------------------
# 5. Isolated Agency Partner Portal Endpoints (PII Sanitized)
# -----------------------------------------------------------------------------

@router.get("/portal/overview")
async def get_agency_portal_overview(
    db: AsyncSession = Depends(get_db),
):
    """Returns partner agency workspace metrics and operational status."""
    return {
        "agency_name": "GrowthCraft Media Labs",
        "verification_status": "verified",
        "badge": "MarketPath Certified Growth Partner",
        "active_client_briefs_count": 5,
        "inquiries_received_count": 14,
        "proposals_sent_count": 9,
        "rating_avg": 4.9,
        "reviews_count": 28,
        "total_gmv_managed": "₹1.48 Cr",
        "partner_tier": "Premier D2C Specialist",
    }


@router.get("/portal/briefs")
async def list_agency_portal_client_briefs(
    db: AsyncSession = Depends(get_db),
):
    """Returns seller client briefs sanitized of founder personal phone, private email, and margins."""
    raw_briefs = [
        {
            "id": "brf-001",
            "brand_name": "Aura Terra Living",
            "category": "Home & Living / Decor",
            "business_stage": "Early Revenue (₹5L - ₹20L / mo)",
            "budget_tier": "₹50,000 - ₹1,50,000 / month",
            "marketing_objectives": ["Scale Meta Ads ROAS to 4x", "Creative static & UGC carousels"],
            "required_services": ["Performance Advertising", "Content Production", "Shopify CRO"],
            "target_timeline": "Within 2 weeks",
            "founder_phone": "+91 9823012345",
            "founder_email": "ananya.deshmukh@auraterra.in",
            "cost_price": 320,
            "margin_percentage": 68,
            "created_at": "2026-11-08T10:30:00Z",
        },
        {
            "id": "brf-002",
            "brand_name": "Veda Botanicals",
            "category": "Clean Skincare & Beauty",
            "business_stage": "Scaling (₹20L - ₹50L / mo)",
            "budget_tier": "₹1,50,000 - ₹3,00,000 / month",
            "marketing_objectives": ["Amazon Ads SP-API optimization", "Influencer seeding on Instagram"],
            "required_services": ["Marketplace Ad Management", "Influencer Marketing"],
            "target_timeline": "Immediate (Festive Season)",
            "founder_phone": "+91 9988776655",
            "founder_email": "rohit.gupta@vedabotanicals.com",
            "cost_price": 180,
            "margin_percentage": 75,
            "created_at": "2026-11-09T14:15:00Z",
        },
        {
            "id": "brf-003",
            "brand_name": "Kaveri Chai Co.",
            "category": "Specialty Tea & Single-Origin Coffee",
            "business_stage": "Pre-launch / Seed",
            "budget_tier": "₹25,000 - ₹50,000 / month",
            "marketing_objectives": ["Brand launch storytelling", "D2C subscription setup"],
            "required_services": ["Brand Identity Strategy", "Performance Advertising"],
            "target_timeline": "Next month",
            "founder_phone": "+91 9765432109",
            "founder_email": "meera.iyer@kaverichai.in",
            "cost_price": 90,
            "margin_percentage": 60,
            "created_at": "2026-11-10T08:00:00Z",
        },
    ]

    # Apply strict PII sanitization to all client briefs
    return [sanitize_client_brief(b) for b in raw_briefs]


@router.get("/portal/packages")
async def list_agency_portal_packages():
    """Lists published service and pricing packages for the agency portal."""
    return [
        {
            "id": "pkg-01",
            "name": "Starter D2C Retainer",
            "monthly_retainer_inr": 45000,
            "best_for": "Emerging brands scaling from ₹5L to ₹20L monthly GMV",
            "deliverables": [
                "Full Meta Ads management (up to ₹2L monthly media spend)",
                "8 custom static & carousel creatives per month",
                "Bi-weekly live performance & ROAS reporting call",
                "Shopify product page conversion audit",
            ],
            "turnaround_days": 7,
            "active_clients": 6,
        },
        {
            "id": "pkg-02",
            "name": "Scale-Up Performance & Creative Growth",
            "monthly_retainer_inr": 95000,
            "best_for": "Established D2C brands scaling ₹20L to ₹1 Cr monthly GMV",
            "deliverables": [
                "Omnichannel paid ads (Meta Ads + Google Shopping & P-Max)",
                "16 bespoke ad creatives (UGC hooks, lifestyle, unboxing)",
                "Weekly sprint calls & dedicated Slack channel",
                "Full attribution audit & creative testing framework",
            ],
            "turnaround_days": 5,
            "active_clients": 11,
        },
        {
            "id": "pkg-03",
            "name": "Marketplace Acceleration (Amazon + Quick Commerce)",
            "monthly_retainer_inr": 60000,
            "best_for": "Brands expanding onto Amazon.in, Blinkit & Zepto",
            "deliverables": [
                "Amazon SP-API Sponsored Products & Brands management",
                "A+ Enhanced Brand Content & Storefront design",
                "Quick commerce dark store inventory forecasting",
                "Listing keyword indexing & SEO optimization",
            ],
            "turnaround_days": 10,
            "active_clients": 4,
        },
    ]


@router.post("/portal/packages", status_code=status.HTTP_201_CREATED)
async def create_agency_portal_package(
    payload: Dict[str, Any],
):
    """Creates a new service package in the agency portal workspace."""
    new_pkg = {
        "id": f"pkg-{uuid.uuid4().hex[:6]}",
        "name": payload.get("name", "Custom Growth Retainer"),
        "monthly_retainer_inr": payload.get("monthly_retainer_inr") or payload.get("price_inr", 35000),
        "best_for": payload.get("best_for", "Emerging D2C Brands"),
        "deliverables": payload.get("deliverables", ["Monthly strategy & performance reports"]),
        "turnaround_days": payload.get("turnaround_days", 14),
        "active_clients": 0,
    }
    return new_pkg


@router.get("/portal/portfolio")
async def list_agency_portal_portfolio():
    """Returns agency case studies clearly tagged as Verified or Demo."""
    return [
        {
            "id": "port-01",
            "client_name": "Aura Terra Living",
            "category": "Home & Living / Decor",
            "headline": "Scaled D2C Shopify sales by 240% in 90 days at 3.8x ROAS",
            "metrics": {"roas": "3.8x", "gmv_growth": "+240%", "blended_cac": "₹320"},
            "is_demo_work": False,
            "verification_badge": "Verified MarketPath Brand Client",
        },
        {
            "id": "port-02",
            "client_name": "Lumina Silk Studio (Demo Case)",
            "category": "Sustainable Fashion & Apparel",
            "headline": "Full-funnel creative testing framework generated 4.2x ROAS",
            "metrics": {"roas": "4.2x", "gmv_growth": "+180%", "blended_cac": "₹410"},
            "is_demo_work": True,
            "verification_badge": "Demo Portfolio Case Study",
        },
    ]


@router.post("/portal/portfolio", status_code=status.HTTP_201_CREATED)
async def create_agency_portal_portfolio_case(
    payload: Dict[str, Any],
):
    """Submits a case study to the agency portfolio with explicit Demo Sample / Verified badge."""
    is_demo = bool(payload.get("is_demo_work", True))
    new_case = {
        "id": f"port-{uuid.uuid4().hex[:6]}",
        "client_name": payload.get("client_name", "Demo Brand"),
        "category": payload.get("category", "D2C General"),
        "headline": payload.get("headline", "Growth case study"),
        "metrics": payload.get("metrics", {"roas": "3.5x"}),
        "is_demo_work": is_demo,
        "verification_badge": "Demo Portfolio Case Study" if is_demo else "Verified MarketPath Brand Client",
    }
    return new_case

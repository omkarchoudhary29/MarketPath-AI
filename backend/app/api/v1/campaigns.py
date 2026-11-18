import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, get_current_tenant_context, require_role
from backend.app.models.brand import BrandProfile
from backend.app.models.catalogue import Product
from backend.app.schemas.marketing import (
    CampaignAIPlanRequest,
    CampaignAIProposal,
    CampaignApprovalRequest,
    CampaignControlRequest,
    CampaignCreate,
    CampaignPerformanceSummary,
    CampaignRead,
    CampaignUpdate,
    ManualExecutionPack,
    ProductSummary,
)
from backend.app.services.campaign_planner_service import generate_campaign_plan
from backend.app.services.marketing_service import CampaignNotFoundError, MarketingService

router = APIRouter(prefix="/campaigns", tags=["Marketing & Campaigns"])


def _format_campaign_read(campaign, perf_summary=None) -> CampaignRead:
    prod_summary = None
    if "product" in campaign.__dict__ and campaign.product:
        prod = campaign.product
        thumb = None
        if "media" in prod.__dict__ and prod.media:
            thumb = prod.media[0].url
        prod_summary = ProductSummary(
            id=prod.id,
            title=prod.title,
            sku=prod.sku,
            category=prod.category,
            base_price=float(prod.base_price),
            currency=prod.currency,
            thumbnail_url=thumb,
        )

    return CampaignRead(
        id=campaign.id,
        organization_id=campaign.organization_id,
        product_id=campaign.product_id,
        name=campaign.name,
        objective=campaign.objective,
        channel=campaign.channel,
        target_geography=campaign.target_geography,
        target_audience_brief=campaign.target_audience_brief,
        landing_page_url=campaign.landing_page_url,
        call_to_action=campaign.call_to_action,
        creative_format=campaign.creative_format,
        description=campaign.description,
        total_budget=float(campaign.total_budget),
        daily_budget_limit=float(campaign.daily_budget_limit),
        currency=campaign.currency,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        status=campaign.status,
        approved_by_user_id=campaign.approved_by_user_id,
        approved_at=campaign.approved_at,
        utm_params=campaign.utm_params,
        ai_proposal=campaign.ai_proposal,
        manual_setup_instructions=campaign.manual_setup_instructions,
        rejection_reason=campaign.rejection_reason,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        product=prod_summary,
        creatives=[c for c in campaign.creatives],
        performance_summary=perf_summary,
    )


@router.get("", response_model=List[CampaignRead])
async def list_campaigns(
    status: Optional[str] = Query(None, description="Filter by status: draft, approved, active, paused, completed"),
    channel: Optional[str] = Query(None, description="Filter by channel: meta_ads, google_ads"),
    search: Optional[str] = Query(None, description="Search by campaign name"),
    ctx: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists all marketing campaigns for the active organization."""
    service = MarketingService(db)
    campaigns = await service.list_campaigns(
        organization_id=ctx.organization_id,
        status=status,
        channel=channel,
        search=search,
    )
    return [_format_campaign_read(c) for c in campaigns]


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    ctx: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new marketing campaign brief with budget pacing limits."""
    service = MarketingService(db)
    try:
        campaign = await service.create_campaign(
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            payload=payload,
        )
        return _format_campaign_read(campaign)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/plan", response_model=CampaignAIProposal)
async def generate_ai_campaign_plan(
    payload: CampaignAIPlanRequest,
    ctx: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Uses Gemini AI to generate a grounded, structured campaign strategy without hallucinated benchmarks."""
    product = None
    if payload.product_id:
        p_res = await db.execute(
            select(Product).where(Product.id == payload.product_id, Product.organization_id == ctx.organization_id)
        )
        product = p_res.scalar_one_or_none()

    b_res = await db.execute(
        select(BrandProfile).where(BrandProfile.organization_id == ctx.organization_id)
    )
    brand = b_res.scalar_one_or_none()

    proposal, _, _ = await generate_campaign_plan(product=product, brand=brand, req=payload)
    return proposal


@router.get("/overview/stats")
async def get_marketing_overview(
    ctx: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Aggregates high-level marketing overview statistics across all campaigns for the organization."""
    service = MarketingService(db)
    campaigns = await service.list_campaigns(organization_id=ctx.organization_id)

    total_campaigns = len(campaigns)
    active_campaigns = sum(1 for c in campaigns if c.status == "active")
    approved_campaigns = sum(1 for c in campaigns if c.status in ("approved", "ready_for_manual_setup"))
    paused_campaigns = sum(1 for c in campaigns if c.status == "paused")

    total_allocated_budget = sum(float(c.total_budget) for c in campaigns)
    total_spend = 0.0
    total_impressions = 0
    total_clicks = 0
    total_conversions = 0
    total_conversion_value = 0.0

    for c in campaigns:
        for ext in c.external_deployments:
            for dm in ext.daily_metrics:
                spend_val = float(dm.spend)
                total_spend += spend_val
                total_impressions += dm.impressions
                total_clicks += dm.clicks
                total_conversions += dm.conversions
                total_conversion_value += float(dm.conversion_value)

    blended_ctr = (total_clicks / total_impressions * 100.0) if total_impressions > 0 else 0.0
    blended_roas = (total_conversion_value / total_spend) if total_spend > 0 else None

    return {
        "total_campaigns": total_campaigns,
        "active_campaigns": active_campaigns,
        "approved_campaigns": approved_campaigns,
        "paused_campaigns": paused_campaigns,
        "total_allocated_budget_inr": round(total_allocated_budget, 2),
        "total_spend_inr": round(total_spend, 2),
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "total_conversion_value_inr": round(total_conversion_value, 2),
        "blended_ctr": round(blended_ctr, 2),
        "blended_roas": round(blended_roas, 2) if blended_roas else None,
        "currency": "INR",
    }


@router.get("/{id}", response_model=CampaignRead)
async def get_campaign_detail(
    id: uuid.UUID,
    ctx: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Fetches comprehensive campaign details, creatives, and deterministic performance summary."""
    service = MarketingService(db)
    campaign = await service.get_campaign(campaign_id=id, organization_id=ctx.organization_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    perf_summary = await service.get_performance_summary(campaign)
    return _format_campaign_read(campaign, perf_summary)


@router.put("/{id}", response_model=CampaignRead)
async def update_campaign(
    id: uuid.UUID,
    payload: CampaignUpdate,
    ctx: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Updates campaign parameters and brief."""
    service = MarketingService(db)
    try:
        campaign = await service.update_campaign(
            campaign_id=id,
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            payload=payload,
        )
        return _format_campaign_read(campaign)
    except CampaignNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/approve")
async def approve_campaign(
    id: uuid.UUID,
    payload: CampaignApprovalRequest,
    ctx: TenantContext = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Explicit human-in-the-loop owner/admin budget authorization. Required before any campaign launch."""
    service = MarketingService(db)
    try:
        campaign, manual_pack = await service.approve_campaign_budget(
            campaign_id=id,
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            approval_req=payload,
        )
        return {
            "success": True,
            "message": "Campaign budget authorized by owner.",
            "campaign": _format_campaign_read(campaign),
            "manual_execution_pack": manual_pack.model_dump(mode="json") if manual_pack else None,
        }
    except CampaignNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/launch")
async def launch_campaign(
    id: uuid.UUID,
    ad_account_id: Optional[str] = Query(None, description="Target ad account ID"),
    ctx: TenantContext = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Launches campaign via official Meta Marketing API or prepares manual launch pack."""
    service = MarketingService(db)
    try:
        result = await service.launch_campaign(
            campaign_id=id,
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            ad_account_id=ad_account_id,
        )
        return result
    except CampaignNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/pause", response_model=CampaignRead)
async def pause_campaign(
    id: uuid.UUID,
    payload: Optional[CampaignControlRequest] = None,
    ctx: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Immediately stops ad pacing and sets campaign status to paused."""
    service = MarketingService(db)
    try:
        reason = payload.reason if payload else "User requested pause"
        campaign = await service.pause_campaign(
            campaign_id=id,
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            reason=reason,
        )
        return _format_campaign_read(campaign)
    except CampaignNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/resume", response_model=CampaignRead)
async def resume_campaign(
    id: uuid.UUID,
    ctx: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Resumes spend for a paused approved campaign."""
    service = MarketingService(db)
    try:
        campaign = await service.resume_campaign(
            campaign_id=id,
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
        )
        return _format_campaign_read(campaign)
    except CampaignNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/stop", response_model=CampaignRead)
async def stop_campaign(
    id: uuid.UUID,
    payload: Optional[CampaignControlRequest] = None,
    ctx: TenantContext = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Permanently completes and deactivates a campaign."""
    service = MarketingService(db)
    try:
        reason = payload.reason if payload else "Campaign finished"
        campaign = await service.stop_campaign(
            campaign_id=id,
            organization_id=ctx.organization_id,
            user_id=ctx.user.id,
            reason=reason,
        )
        return _format_campaign_read(campaign)
    except CampaignNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{id}/export", response_model=ManualExecutionPack)
async def export_manual_setup_pack(
    id: uuid.UUID,
    ctx: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Exports structured manual ad setup instructions, targeting checklist, and UTM-tagged creative assets."""
    service = MarketingService(db)
    campaign = await service.get_campaign(campaign_id=id, organization_id=ctx.organization_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    selected_creative = next((c for c in campaign.creatives if c.is_selected), None)
    if not selected_creative and campaign.creatives:
        selected_creative = campaign.creatives[0]

    return service.meta_ads_service.generate_manual_setup_pack(campaign, selected_creative)


@router.get("/{id}/metrics", response_model=CampaignPerformanceSummary)
async def get_campaign_metrics(
    id: uuid.UUID,
    ctx: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Fetches deterministic performance metrics with source attribution."""
    service = MarketingService(db)
    campaign = await service.get_campaign(campaign_id=id, organization_id=ctx.organization_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    return await service.get_performance_summary(campaign)

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.schemas.analytics import (
    AIAssistantRequest,
    AIAssistantResponse,
    AnalyticsOverviewRead,
    MarketingAnalyticsResponse,
    ProductAnalyticsResponse,
    PublishingAnalyticsResponse,
)
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Unified Grounded Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewRead)
async def get_analytics_overview(
    time_range: str = Query("Last 30 Days", description="7 Days, 30 Days, 90 Days, YTD"),
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Returns deterministic business, marketing, and omnichannel publishing overview."""
    return await AnalyticsService.get_overview(db, context.organization_id, time_range)


@router.get("/products", response_model=ProductAnalyticsResponse)
async def get_product_analytics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Returns product-level publishing coverage, variant breakdowns, and pricing."""
    return await AnalyticsService.get_product_analytics(
        db, context.organization_id, page=page, page_size=page_size
    )


@router.get("/publishing", response_model=PublishingAnalyticsResponse)
async def get_publishing_analytics(
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Returns omnichannel publishing job success/failure rates and channel telemetry."""
    return await AnalyticsService.get_publishing_analytics(db, context.organization_id)


@router.get("/marketing", response_model=MarketingAnalyticsResponse)
async def get_marketing_analytics(
    time_range: str = Query("Last 30 Days"),
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Returns campaign-level advertising performance and daily telemetry."""
    return await AnalyticsService.get_marketing_analytics(db, context.organization_id, time_range)


@router.post("/ai-assistant", response_model=AIAssistantResponse)
async def ask_analytics_ai_assistant(
    request: AIAssistantRequest,
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Queries the AI analytics assistant grounded strictly in verified organization numbers."""
    return await AnalyticsService.ask_ai_assistant(
        db,
        context.organization_id,
        question=request.question,
        time_range=request.time_range,
        channel_filter=request.channel_filter,
    )


import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalyticsOverviewRead(BaseModel):
    organization_id: uuid.UUID
    date_range: str
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"
    last_synced_at: Optional[datetime.datetime] = None
    attribution_window: str = "7-day click / 1-day view"
    data_source: str = "DETERMINISTIC_DATABASE"

    # Business Overview KPIs
    total_products: int
    active_products: int
    published_products: int
    failed_publishing_jobs: int
    connected_channels_count: int
    active_campaigns_count: int

    # Omnichannel Order & Sales KPIs
    total_orders: int = 0
    gross_sales_inr: float = 0.0
    net_sales_inr: float = 0.0
    total_revenue_inr: float = 0.0
    units_sold: int = 0
    average_order_value: float = 0.0
    gross_merchandise_sales_inr: float = 0.0
    discounts_inr: float = 0.0
    refunds_inr: float = 0.0
    shipping_inr: float = 0.0
    taxes_inr: float = 0.0
    channel_sales_breakdown: List[Dict[str, Any]] = Field(default_factory=list)

    # Marketing Aggregates
    total_spend: float
    total_impressions: int
    total_reach: int
    total_clicks: int
    average_ctr: float
    average_cpc: float
    total_conversions: int
    total_conversion_value: float
    roas: float

    # Publishing Aggregates
    publishing_stats: Dict[str, int]  # {"total": X, "completed": Y, "failed": Z, "queued": W}

    # Connected Channels List
    connected_channels: List[Dict[str, Any]]


class ProductAnalyticsItem(BaseModel):
    product_id: uuid.UUID
    title: str
    sku: Optional[str] = None
    price_inr: float
    status: str
    is_active: bool
    variants_count: int
    listings_count: int
    published_channels: List[str]
    total_orders_recorded: int = 0
    total_sales_recorded_inr: float = 0.0
    sync_status: str


class ProductAnalyticsResponse(BaseModel):
    items: List[ProductAnalyticsItem]
    total_count: int
    page: int
    page_size: int
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"


class PublishingAnalyticsItem(BaseModel):
    channel: str
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    pending_jobs: int
    success_rate: float
    last_published_at: Optional[datetime.datetime] = None


class PublishingAnalyticsResponse(BaseModel):
    channels: List[PublishingAnalyticsItem]
    recent_jobs: List[Dict[str, Any]]
    total_attempts: int
    overall_success_rate: float


class MarketingAnalyticsDaily(BaseModel):
    date: datetime.date
    spend: float
    impressions: int
    clicks: int
    conversions: int
    conversion_value: float
    ctr: float
    cpc: float
    roas: float


class MarketingAnalyticsCampaign(BaseModel):
    campaign_id: uuid.UUID
    name: str
    channel: str
    status: str
    spend: float
    impressions: int
    clicks: int
    conversions: int
    conversion_value: float
    ctr: float
    cpc: float
    roas: float


class MarketingAnalyticsResponse(BaseModel):
    date_range: str
    currency: str = "INR"
    summary: Dict[str, Any]
    daily_breakdown: List[MarketingAnalyticsDaily]
    campaigns: List[MarketingAnalyticsCampaign]


class AIAssistantRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    time_range: str = Field("Last 30 Days", max_length=50)
    channel_filter: Optional[str] = "All Channels"


class AIAssistantResponse(BaseModel):
    question: str
    answer: str
    grounding_data: Dict[str, Any]
    data_sources: List[str]
    time_range: str
    generated_at: datetime.datetime


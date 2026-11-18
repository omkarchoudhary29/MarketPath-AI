import datetime
import uuid
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==========================================
# Creative Schemas
# ==========================================

class CampaignCreativeCreate(BaseModel):
    headline: str = Field(..., min_length=2, max_length=255)
    primary_text: str = Field(..., min_length=5)
    description_text: Optional[str] = None
    cta_text: str = Field(default="Shop Now", max_length=50)
    media_url: str = Field(..., min_length=5)
    destination_url: str = Field(..., min_length=5)
    format: str = Field(default="feed_image", max_length=50)  # feed_image, story, carousel
    version_number: int = Field(default=1, ge=1)
    is_selected: bool = True
    is_approved: bool = False


class CampaignCreativeRead(CampaignCreativeCreate):
    id: uuid.UUID
    campaign_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class CreativeGenerateRequest(BaseModel):
    product_id: uuid.UUID
    campaign_objective: Optional[str] = "sales"
    creative_format: Optional[str] = "feed_image"
    selected_media_urls: Optional[List[str]] = Field(default_factory=list)
    tone_override: Optional[str] = None


# ==========================================
# AI Campaign Planner Schemas (PART 4)
# ==========================================

class CampaignAIPlanRequest(BaseModel):
    natural_language_brief: Optional[str] = Field(
        None,
        description="Free-form brief from seller e.g. 'Promote bamboo boxes to premium gifting customers in Maharashtra'"
    )
    product_id: Optional[uuid.UUID] = None
    objective: Optional[Literal["awareness", "traffic", "engagement", "leads", "sales"]] = "sales"
    target_geography: Optional[str] = "Pan-India"
    target_audience: Optional[str] = None
    monthly_budget_inr: Optional[float] = Field(default=10000.0, ge=500.0)
    duration_days: Optional[int] = Field(default=30, ge=1, le=365)
    channel: Optional[Literal["meta_ads", "google_ads"]] = "meta_ads"


class CreativeConcept(BaseModel):
    concept_title: str
    visual_direction: str
    hook_angle: str
    recommended_format: str = "feed_image"


class CampaignScheduleItem(BaseModel):
    phase: str
    day_range: str
    phase_objective: str
    action_items: List[str]


class CampaignAIProposal(BaseModel):
    strategy_summary: str
    objective_interpretation: str
    suggested_channel: str
    channel_rationale: str
    target_audience_hypotheses: List[str]
    geography_recommendations: List[str]
    ad_headlines: List[str]
    primary_texts: List[str]
    creative_concepts: List[CreativeConcept]
    call_to_action_options: List[str]
    suggested_budget_allocation: Dict[str, Any]
    campaign_schedule: List[CampaignScheduleItem]
    measurement_strategy: Dict[str, Any]
    assumptions_and_risks: List[str]
    missing_information_notes: Optional[str] = None
    disclaimer: str = Field(
        default="AI-generated hypothesis based on seller brief. Benchmarks, conversions, and ROAS are not guaranteed and must be verified in live ad account tests."
    )
    is_mock: bool = False


# ==========================================
# Campaign CRUD Schemas
# ==========================================

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    product_id: Optional[uuid.UUID] = None
    objective: Literal["awareness", "traffic", "engagement", "leads", "sales"] = "sales"
    channel: Literal["meta_ads", "google_ads"] = "meta_ads"
    target_geography: Optional[str] = "Pan-India"
    target_audience_brief: Optional[str] = None
    landing_page_url: Optional[str] = None
    call_to_action: Optional[str] = "Shop Now"
    creative_format: Optional[str] = "feed_image"
    description: Optional[str] = None
    total_budget: float = Field(..., gt=0)
    daily_budget_limit: float = Field(..., gt=0)
    currency: str = Field(default="INR", max_length=3)
    start_date: datetime.date
    end_date: Optional[datetime.date] = None
    utm_params: Optional[Dict[str, str]] = None
    ai_proposal: Optional[Dict[str, Any]] = None
    creatives: Optional[List[CampaignCreativeCreate]] = Field(default_factory=list)

    @field_validator("daily_budget_limit")
    @classmethod
    def validate_daily_budget(cls, v: float) -> float:
        if v < 100.0:
            raise ValueError("Daily budget limit must be at least ₹100.00.")
        return v

    @field_validator("total_budget")
    @classmethod
    def validate_total_budget(cls, v: float, values: Any) -> float:
        # Pydantic v2 validation
        return v


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    product_id: Optional[uuid.UUID] = None
    objective: Optional[Literal["awareness", "traffic", "engagement", "leads", "sales"]] = None
    channel: Optional[Literal["meta_ads", "google_ads"]] = None
    target_geography: Optional[str] = None
    target_audience_brief: Optional[str] = None
    landing_page_url: Optional[str] = None
    call_to_action: Optional[str] = None
    creative_format: Optional[str] = None
    description: Optional[str] = None
    total_budget: Optional[float] = Field(None, gt=0)
    daily_budget_limit: Optional[float] = Field(None, gt=0)
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    utm_params: Optional[Dict[str, str]] = None
    ai_proposal: Optional[Dict[str, Any]] = None


class CampaignApprovalRequest(BaseModel):
    approved: bool = True
    approved_budget_cap: Optional[float] = None
    notes: Optional[str] = None


class CampaignControlRequest(BaseModel):
    action: Literal["pause", "resume", "stop"]
    reason: Optional[str] = None


# ==========================================
# Manual Execution & Performance Schemas
# ==========================================

class ManualExecutionPack(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str
    channel: str
    objective: str
    target_geography: str
    targeting_checklist: Dict[str, Any]
    budget_and_schedule: Dict[str, Any]
    copy_and_creatives: List[Dict[str, Any]]
    utm_tagged_destination_url: str
    step_by_step_instructions: List[str]
    setup_status: str = "Ready for Manual Setup"
    generated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class CampaignMetricsRead(BaseModel):
    date: datetime.date
    spend: float
    impressions: int
    clicks: int
    reach: Optional[int] = 0
    conversions: int
    conversion_value: float
    ctr: float = 0.0  # percentage
    cpc: float = 0.0
    roas: Optional[float] = None
    synced_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignPerformanceSummary(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str
    status: str
    currency: str
    total_spend: float
    total_budget: float
    remaining_budget: float
    daily_budget_limit: float
    total_impressions: int
    total_clicks: int
    total_reach: int
    total_conversions: int
    total_conversion_value: float
    average_ctr: float
    average_cpc: float
    blended_roas: Optional[float]
    data_source: str
    attribution_window: str = "7-day click / 1-day view"
    last_synced_at: Optional[datetime.datetime]
    daily_breakdown: List[CampaignMetricsRead] = Field(default_factory=list)


class ProductSummary(BaseModel):
    id: uuid.UUID
    title: str
    sku: str
    category: str
    base_price: float
    currency: str
    thumbnail_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CampaignRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    product_id: Optional[uuid.UUID]
    name: str
    objective: str
    channel: str
    target_geography: Optional[str]
    target_audience_brief: Optional[str]
    landing_page_url: Optional[str]
    call_to_action: Optional[str]
    creative_format: Optional[str]
    description: Optional[str]
    total_budget: float
    daily_budget_limit: float
    currency: str
    start_date: datetime.date
    end_date: Optional[datetime.date]
    status: str
    approved_by_user_id: Optional[uuid.UUID]
    approved_at: Optional[datetime.datetime]
    utm_params: Optional[Dict[str, Any]]
    ai_proposal: Optional[Dict[str, Any]]
    manual_setup_instructions: Optional[Dict[str, Any]]
    rejection_reason: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    product: Optional[ProductSummary] = None
    creatives: List[CampaignCreativeRead] = Field(default_factory=list)
    performance_summary: Optional[CampaignPerformanceSummary] = None

    model_config = ConfigDict(from_attributes=True)


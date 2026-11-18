import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ---------------------------------------------------------
# Agency Services & Packages Schemas
# ---------------------------------------------------------

class AgencyServiceBase(BaseModel):
    name: str = Field(..., max_length=150)
    category: str = Field(..., max_length=100)
    description: str
    deliverables: List[str] = Field(default_factory=list)
    pricing_model: str = Field("monthly_retainer", description="monthly_retainer, project_based, one_time")
    min_price_inr: int = Field(..., ge=0)
    max_price_inr: Optional[int] = Field(None, ge=0)
    estimated_duration: str = Field("Ongoing monthly", max_length=100)
    target_industries: List[str] = Field(default_factory=list)
    is_available: bool = True


class AgencyServiceCreate(AgencyServiceBase):
    pass


class AgencyServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    deliverables: Optional[List[str]] = None
    pricing_model: Optional[str] = None
    min_price_inr: Optional[int] = None
    max_price_inr: Optional[int] = None
    estimated_duration: Optional[str] = None
    target_industries: Optional[List[str]] = None
    is_available: Optional[bool] = None


class AgencyServiceRead(AgencyServiceBase):
    id: uuid.UUID
    agency_profile_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class AgencyPackageBase(BaseModel):
    name: str = Field(..., max_length=150)
    package_tier: str = Field("growth", description="starter, growth, premium, custom")
    price_inr: int = Field(..., ge=0)
    billing_interval: str = Field("monthly", description="monthly, one_time, project")
    description: str
    deliverables: List[str] = Field(default_factory=list)
    turnaround_days: int = Field(30, ge=1)
    is_active: bool = True


class AgencyPackageCreate(AgencyPackageBase):
    service_id: Optional[uuid.UUID] = None


class AgencyPackageUpdate(BaseModel):
    name: Optional[str] = None
    package_tier: Optional[str] = None
    price_inr: Optional[int] = None
    billing_interval: Optional[str] = None
    description: Optional[str] = None
    deliverables: Optional[List[str]] = None
    turnaround_days: Optional[int] = None
    is_active: Optional[bool] = None


class AgencyPackageRead(AgencyPackageBase):
    id: uuid.UUID
    agency_profile_id: uuid.UUID
    service_id: Optional[uuid.UUID] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Agency Portfolio Schemas
# ---------------------------------------------------------

class AgencyPortfolioBase(BaseModel):
    client_brand_name: str = Field(..., max_length=150)
    category: str = Field(..., max_length=100)
    project_title: str = Field(..., max_length=200)
    description: str
    case_study_url: Optional[str] = None
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    media_urls: List[str] = Field(default_factory=list)
    display_order: int = 0


class AgencyPortfolioCreate(AgencyPortfolioBase):
    pass


class AgencyPortfolioUpdate(BaseModel):
    client_brand_name: Optional[str] = None
    category: Optional[str] = None
    project_title: Optional[str] = None
    description: Optional[str] = None
    case_study_url: Optional[str] = None
    key_metrics: Optional[Dict[str, Any]] = None
    media_urls: Optional[List[str]] = None
    display_order: Optional[int] = None


class AgencyPortfolioRead(AgencyPortfolioBase):
    id: uuid.UUID
    agency_profile_id: uuid.UUID
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Agency Profile Schemas
# ---------------------------------------------------------

class AgencyProfileBase(BaseModel):
    name: str = Field(..., max_length=150)
    slug: str = Field(..., max_length=100)
    tagline: str = Field(..., max_length=255)
    description: str
    logo_url: Optional[str] = None
    website: Optional[str] = None
    email: str = Field(..., max_length=255)
    phone: Optional[str] = None
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    country: str = "India"
    remote_or_local: str = Field("both", description="remote, local, both")
    team_size: str = Field("1-10", description="1-10, 11-50, 51-200, 200+")
    founded_year: int = 2020
    category_specialties: List[str] = Field(default_factory=list)
    service_offerings: List[str] = Field(default_factory=list)
    min_budget_inr: int = Field(10000, ge=0)
    max_budget_inr: Optional[int] = None
    gst_number: Optional[str] = None
    is_available: bool = True


class AgencyProfileCreate(AgencyProfileBase):
    pass


class AgencyProfileUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    remote_or_local: Optional[str] = None
    team_size: Optional[str] = None
    founded_year: Optional[int] = None
    category_specialties: Optional[List[str]] = None
    service_offerings: Optional[List[str]] = None
    min_budget_inr: Optional[int] = None
    max_budget_inr: Optional[int] = None
    gst_number: Optional[str] = None
    is_available: Optional[bool] = None


class AgencyProfileRead(AgencyProfileBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    verification_status: str
    verification_notes: Optional[str] = None
    verified_at: Optional[datetime.datetime] = None
    is_active: bool
    is_featured: bool
    is_demo: bool
    tier: str
    rating_avg: float
    reviews_count: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class AgencyProfileDetailRead(AgencyProfileRead):
    services: List[AgencyServiceRead] = Field(default_factory=list)
    packages: List[AgencyPackageRead] = Field(default_factory=list)
    portfolios: List[AgencyPortfolioRead] = Field(default_factory=list)


# ---------------------------------------------------------
# Seller Requirement Schemas & AI Extraction
# ---------------------------------------------------------

class SellerRequirementBase(BaseModel):
    brand_name: str = Field(..., max_length=150)
    product_category: str = Field(..., max_length=100)
    business_stage: str = Field(..., max_length=100)
    location: str = Field(..., max_length=100)
    website: Optional[str] = None
    sales_channels: List[str] = Field(default_factory=list)
    catalogue_size: Optional[int] = None
    target_market: Optional[str] = None
    business_objectives: List[str] = Field(default_factory=list)
    required_services: List[str] = Field(default_factory=list)
    monthly_budget_inr: Optional[int] = None
    project_budget_inr: Optional[int] = None
    total_budget_inr: Optional[int] = None
    currency: str = "INR"
    engagement_duration: Optional[str] = None
    preferred_location: Optional[str] = None
    remote_or_local: str = "both"
    industry_experience_required: Optional[str] = None
    preferred_agency_size: Optional[str] = None
    expected_start_date: Optional[str] = None
    special_requirements: Optional[str] = None


class SellerRequirementCreate(SellerRequirementBase):
    ai_search_brief: Optional[str] = None
    ai_suggested_services: List[str] = Field(default_factory=list)


class SellerRequirementUpdate(BaseModel):
    brand_name: Optional[str] = None
    product_category: Optional[str] = None
    business_stage: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    sales_channels: Optional[List[str]] = None
    catalogue_size: Optional[int] = None
    target_market: Optional[str] = None
    business_objectives: Optional[List[str]] = None
    required_services: Optional[List[str]] = None
    monthly_budget_inr: Optional[int] = None
    project_budget_inr: Optional[int] = None
    total_budget_inr: Optional[int] = None
    engagement_duration: Optional[str] = None
    preferred_location: Optional[str] = None
    remote_or_local: Optional[str] = None
    industry_experience_required: Optional[str] = None
    preferred_agency_size: Optional[str] = None
    expected_start_date: Optional[str] = None
    special_requirements: Optional[str] = None
    ai_search_brief: Optional[str] = None
    ai_suggested_services: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SellerRequirementRead(SellerRequirementBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    ai_search_brief: Optional[str] = None
    ai_suggested_services: List[str] = Field(default_factory=list)
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class AIRequirementExtractionRequest(BaseModel):
    brand_name: str
    product_category: str
    business_stage: str
    location: str
    raw_brief_text: Optional[str] = None
    selected_objectives: List[str] = Field(default_factory=list)
    selected_services: List[str] = Field(default_factory=list)
    monthly_budget_inr: Optional[int] = None
    project_budget_inr: Optional[int] = None


class AIRequirementExtractionResponse(BaseModel):
    search_brief: str
    detected_category: str
    detected_stage: str
    identified_objectives: List[str]
    identified_services: List[str]
    suggested_additional_services: List[str]
    missing_information_alerts: List[str]
    budget_advisory: str
    is_ai_generated: bool = True


# ---------------------------------------------------------
# Matching & Recommendation Schemas
# ---------------------------------------------------------

class AgencyMatchExplanation(BaseModel):
    why_matched: str
    services_covered: List[str]
    portfolio_highlights: List[str]
    budget_compatibility_note: str
    location_compatibility_note: str
    verification_standing: str
    missing_or_uncertain_info: Optional[str] = None
    score_breakdown: Dict[str, float] = Field(default_factory=dict)


class AgencyMatchCard(BaseModel):
    agency: AgencyProfileRead
    packages: List[AgencyPackageRead] = Field(default_factory=list)
    match_score: int = Field(..., ge=0, le=100)
    is_eligible: bool = True
    explanation: AgencyMatchExplanation
    is_featured: bool = False
    is_saved: bool = False


class AgencyRecommendationResponse(BaseModel):
    total_eligible: int
    matches: List[AgencyMatchCard]
    weights_applied: Dict[str, float]
    filtering_metadata: Dict[str, Any]


# ---------------------------------------------------------
# Quote Requests, Introductions & Engagements Schemas
# ---------------------------------------------------------

class AgencyQuoteRequestCreate(BaseModel):
    agency_profile_id: uuid.UUID
    seller_requirement_id: Optional[uuid.UUID] = None
    project_title: str = Field(..., max_length=200)
    project_description: str
    budget_inr: int = Field(..., ge=0)
    budget_type: str = Field("monthly", description="monthly or one_time")
    timeframe: str = Field(..., max_length=100)
    attachment_urls: List[str] = Field(default_factory=list)
    share_contact_consent: bool = True
    contact_email: str = Field(..., max_length=255)
    contact_phone: Optional[str] = None


class AgencyQuoteRequestUpdate(BaseModel):
    status: Optional[str] = None
    agency_response_notes: Optional[str] = None
    quotation_amount_inr: Optional[int] = None
    quotation_deliverables: Optional[List[str]] = None
    quotation_valid_until: Optional[datetime.datetime] = None


class AgencyQuotationSubmit(BaseModel):
    quotation_amount_inr: int = Field(..., ge=0)
    quotation_deliverables: List[str] = Field(default_factory=list)
    agency_response_notes: str
    quotation_valid_until: Optional[datetime.datetime] = None


class AgencyQuoteRequestRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    agency_profile_id: uuid.UUID
    seller_requirement_id: Optional[uuid.UUID] = None
    project_title: str
    project_description: str
    budget_inr: int
    budget_type: str
    timeframe: str
    attachment_urls: List[str]
    share_contact_consent: bool
    contact_email: str
    contact_phone: Optional[str] = None
    status: str
    agency_response_notes: Optional[str] = None
    quotation_amount_inr: Optional[int] = None
    quotation_deliverables: Optional[List[str]] = None
    quotation_valid_until: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    agency_name: Optional[str] = None
    seller_org_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AgencyEngagementRead(BaseModel):
    id: uuid.UUID
    quote_request_id: uuid.UUID
    organization_id: uuid.UUID
    agency_profile_id: uuid.UUID
    package_id: Optional[uuid.UUID] = None
    agreed_price_inr: int
    billing_type: str
    status: str
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    notes: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    agency_name: Optional[str] = None
    seller_org_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Shortlists & Reviews Schemas
# ---------------------------------------------------------

class AgencySavedShortlistCreate(BaseModel):
    agency_profile_id: uuid.UUID
    notes: Optional[str] = None


class AgencySavedShortlistRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    agency_profile_id: uuid.UUID
    notes: Optional[str] = None
    created_at: datetime.datetime
    agency: Optional[AgencyProfileRead] = None

    model_config = ConfigDict(from_attributes=True)


class AgencyReviewCreate(BaseModel):
    engagement_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5)
    title: str = Field(..., max_length=200)
    review_text: str


class AgencyReviewRead(BaseModel):
    id: uuid.UUID
    engagement_id: uuid.UUID
    organization_id: uuid.UUID
    agency_profile_id: uuid.UUID
    rating: int
    title: str
    review_text: str
    is_verified: bool
    created_at: datetime.datetime
    reviewer_org_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Admin Verification Actions
# ---------------------------------------------------------

class AgencyVerificationAction(BaseModel):
    verification_status: str = Field(..., description="verified, rejected, suspended, verification_pending")
    verification_notes: Optional[str] = None
    is_featured: Optional[bool] = None
    tier: Optional[str] = None

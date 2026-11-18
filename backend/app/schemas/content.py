import datetime
import uuid
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


# --- Structured Content Payloads ---

class ShopifyCopyPayload(BaseModel):
    title: str = Field(..., description="SEO and conversion-optimized Shopify product title")
    short_summary: str = Field(..., description="1-2 sentence compelling product hook")
    body_html: str = Field(..., description="Formatted HTML product description")
    bullet_points: List[str] = Field(default_factory=list, description="Key features, dimensions and craft notes")
    suggested_tags: List[str] = Field(default_factory=list, description="Categorization and search tags")
    meta_title: str = Field(..., description="SEO page title under 60 characters")
    meta_description: str = Field(..., description="SEO meta description under 160 characters")
    grounded_facts: List[str] = Field(default_factory=list, description="Verified facts from product specifications")
    missing_information_notes: Optional[str] = Field(None, description="Any seller details that were absent")


class InstagramPostPayload(BaseModel):
    hook: str = Field(..., description="Thumb-stopping first line")
    caption: str = Field(..., description="Aesthetic narrative caption")
    hashtags: List[str] = Field(default_factory=list, description="Curated discovery hashtags")
    carousel_slides: List[str] = Field(default_factory=list, description="Visual framing recommendations per slide")
    call_to_action: str = Field(..., description="Link-in-bio or save CTA")
    grounded_facts: List[str] = Field(default_factory=list, description="Verified facts from product specifications")
    missing_information_notes: Optional[str] = Field(None, description="Any seller details that were absent")


class AdHookPayload(BaseModel):
    headlines: List[str] = Field(..., description="3-5 punchy headlines under 40 characters")
    primary_texts: List[str] = Field(..., description="2-3 ad copy variations (story, problem-solution, aesthetic)")
    cta_options: List[str] = Field(default_factory=list, description="Conversion CTAs: Shop Now, Explore Collection")
    audience_angle: str = Field(..., description="Target persona justification")
    grounded_facts: List[str] = Field(default_factory=list, description="Verified facts from product specifications")
    missing_information_notes: Optional[str] = Field(None, description="Any seller details that were absent")


class SEOPackPayload(BaseModel):
    seo_title: str = Field(..., description="Target search intent title")
    meta_description: str = Field(..., description="Click-through optimized meta description")
    target_keywords: List[str] = Field(default_factory=list, description="Primary and long-tail keywords")
    url_slug_recommendation: str = Field(..., description="Clean URL slug suggestion")
    grounded_facts: List[str] = Field(default_factory=list, description="Verified facts from product specifications")
    missing_information_notes: Optional[str] = Field(None, description="Any seller details that were absent")


class FullPackPayload(BaseModel):
    shopify: ShopifyCopyPayload
    instagram: InstagramPostPayload
    ad_hooks: AdHookPayload
    seo: SEOPackPayload


# --- Requests & API Envelopes ---

class AIGenerateRequest(BaseModel):
    product_id: uuid.UUID
    target_channel: str = Field("shopify", pattern=r"^(shopify|instagram|meta_ads|google_ads|all)$")
    content_type: str = Field("shopify_copy", pattern=r"^(shopify_copy|instagram_post|ad_hook|seo_pack|full_pack)$")
    tone_override: Optional[str] = Field(None, description="e.g. Warm & Storytelling, Minimal, Vibrant, Festive")
    instructions: Optional[str] = Field(None, description="Custom directives or angles from the seller")
    campaign_objective: Optional[str] = Field("New Product Launch", description="e.g. Festive Gifting, Flash Sale")
    target_audience: Optional[str] = Field(None, description="Target customer segment")


class ContentVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    generation_id: uuid.UUID
    version_number: int
    generated_payload: Dict[str, Any]
    edited_payload: Optional[Dict[str, Any]] = None
    is_approved: bool
    approved_by_user_id: Optional[uuid.UUID] = None
    approved_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime


class ContentVersionUpdate(BaseModel):
    edited_payload: Dict[str, Any]


class ContentApprovalRequest(BaseModel):
    version_id: uuid.UUID
    apply_to_channel_override: bool = Field(
        default=False,
        description="Whether to also copy this approved copy into product_channel_overrides for the target channel"
    )


class ContentRegenerateRequest(BaseModel):
    generation_id: uuid.UUID
    revised_instructions: Optional[str] = None
    tone_override: Optional[str] = None


class ContentGenerationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    product_id: uuid.UUID
    content_type: str
    target_channel: str
    model_version: str
    prompt_snapshot: str
    token_count_input: int
    token_count_output: int
    created_at: datetime.datetime
    versions: List[ContentVersionRead] = Field(default_factory=list)


class AIGenerateResponse(BaseModel):
    generation_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    content_type: str
    target_channel: str
    model_version: str
    tokens_consumed: int
    payload: Dict[str, Any]
    created_at: datetime.datetime


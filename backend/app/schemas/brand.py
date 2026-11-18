import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BrandAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    brand_profile_id: uuid.UUID
    asset_type: str
    asset_url: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime.datetime


class ProductStoryItem(BaseModel):
    product_id: str
    product_title: Optional[str] = None
    origin_story: str
    craftsmanship_notes: Optional[str] = None
    specific_claims: List[str] = Field(default_factory=list)


class BrandProfileBase(BaseModel):
    brand_name: str = Field(..., min_length=2, max_length=150)
    tagline: Optional[str] = Field(None, max_length=255)
    story: Optional[str] = None
    mission: Optional[str] = None
    target_audience: Optional[str] = None
    tone_of_voice: str = Field("Warm & Aesthetic", max_length=50)
    archetype: Optional[str] = Field(None, max_length=50)
    target_audience_summary: Optional[str] = None

    # 15 Revision V2 Dimensions
    visual_guidelines: Dict[str, Any] = Field(default_factory=dict)
    key_usps: List[str] = Field(default_factory=list)
    competitor_differentiation: Optional[str] = None
    brand_values: List[str] = Field(default_factory=list)
    pricing_strategy: Optional[str] = None
    sustainability_practices: Optional[str] = None
    customer_demographics: Dict[str, Any] = Field(default_factory=dict)
    packaging_philosophy: Optional[str] = None
    regulatory_disclaimers: Optional[str] = None
    product_stories: List[Dict[str, Any]] = Field(default_factory=list)


class BrandProfileCreate(BrandProfileBase):
    pass


class BrandProfileUpdate(BaseModel):
    brand_name: Optional[str] = Field(None, min_length=2, max_length=150)
    tagline: Optional[str] = Field(None, max_length=255)
    story: Optional[str] = None
    mission: Optional[str] = None
    target_audience: Optional[str] = None
    tone_of_voice: Optional[str] = Field(None, max_length=50)
    archetype: Optional[str] = Field(None, max_length=50)
    target_audience_summary: Optional[str] = None
    visual_guidelines: Optional[Dict[str, Any]] = None
    key_usps: Optional[List[str]] = None
    competitor_differentiation: Optional[str] = None
    brand_values: Optional[List[str]] = None
    pricing_strategy: Optional[str] = None
    sustainability_practices: Optional[str] = None
    customer_demographics: Optional[Dict[str, Any]] = None
    packaging_philosophy: Optional[str] = None
    regulatory_disclaimers: Optional[str] = None
    product_stories: Optional[List[Dict[str, Any]]] = None


class BrandProfileRead(BrandProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    assets: List[BrandAssetRead] = Field(default_factory=list)
    completeness_score: float = 0.0
    missing_recommended_fields: List[str] = Field(default_factory=list)


class VoiceOnboardRequest(BaseModel):
    raw_transcript: Optional[str] = None
    audio_base64: Optional[str] = None
    duration_seconds: Optional[int] = None


class VoiceExtractionResult(BaseModel):
    brand_name: Optional[str] = None
    tagline: Optional[str] = None
    story: Optional[str] = None
    mission: Optional[str] = None
    tone_of_voice: Optional[str] = None
    archetype: Optional[str] = None
    target_audience_summary: Optional[str] = None
    key_usps: List[str] = Field(default_factory=list)
    brand_values: List[str] = Field(default_factory=list)
    sustainability_practices: Optional[str] = None
    packaging_philosophy: Optional[str] = None
    raw_transcript: str
    confidence_score: float = 0.92


class ProductStoryUpdatePayload(BaseModel):
    origin_story: str
    craftsmanship_notes: Optional[str] = None
    specific_claims: List[str] = Field(default_factory=list)

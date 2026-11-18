import datetime
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.organization import Organization


class BrandProfile(Base, TimestampMixin):
    """Brand identity, creative voice and archetype specifications across 15 dimensions."""
    __tablename__ = "brand_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brand_name: Mapped[str] = mapped_column(String(150), nullable=False)
    tagline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    story: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mission: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tone_of_voice: Mapped[str] = mapped_column(String(50), default="Warm & Aesthetic", nullable=False)
    archetype: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_audience_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Revision V2 Expanded Dimensions
    visual_guidelines: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    key_usps: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    competitor_differentiation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brand_values: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    pricing_strategy: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sustainability_practices: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_demographics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    packaging_philosophy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    regulatory_disclaimers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_stories: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="brand_profiles")
    assets: Mapped[List["BrandAsset"]] = relationship(
        "BrandAsset", back_populates="brand_profile", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<BrandProfile(id={self.id}, name={self.brand_name}, org={self.organization_id})>"


class BrandAsset(Base, TimestampMixin):
    """Brand visual assets (logos, color palettes, fonts)."""
    __tablename__ = "brand_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    brand_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("brand_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # logo, banner, palette, font
    asset_url: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)

    brand_profile: Mapped["BrandProfile"] = relationship("BrandProfile", back_populates="assets")


class BrandVoiceSession(Base):
    """Voice-based onboarding recordings and AI extraction sessions."""
    __tablename__ = "brand_voice_sessions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audio_file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    raw_transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<BrandVoiceSession(id={self.id}, org={self.organization_id}, confirmed={self.is_confirmed})>"

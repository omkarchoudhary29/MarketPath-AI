import datetime
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class AdAccount(Base, TimestampMixin):
    """Connected advertising platform account (Meta Ads, Google Ads)."""
    __tablename__ = "ad_accounts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # meta_ads, google_ads
    external_account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    account_name: Mapped[str] = mapped_column(String(150), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="connected", nullable=False)


class Campaign(Base, TimestampMixin):
    """Marketing and ad campaign strategy record."""
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(String(50), nullable=False)  # awareness, traffic, engagement, leads, sales
    channel: Mapped[str] = mapped_column(String(50), default="meta_ads", nullable=False)
    target_geography: Mapped[Optional[str]] = mapped_column(String(100), default="Pan-India", nullable=True)
    target_audience_brief: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    landing_page_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    call_to_action: Mapped[Optional[str]] = mapped_column(String(50), default="Shop Now", nullable=True)
    creative_format: Mapped[Optional[str]] = mapped_column(String(50), default="feed_image", nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    utm_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    ai_proposal: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    manual_setup_instructions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    total_budget: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    daily_budget_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    product = relationship("Product", foreign_keys=[product_id])
    creatives: Mapped[List["CampaignCreative"]] = relationship(
        "CampaignCreative", back_populates="campaign", cascade="all, delete-orphan"
    )
    external_deployments: Mapped[List["ExternalCampaign"]] = relationship(
        "ExternalCampaign", back_populates="campaign", cascade="all, delete-orphan"
    )


class CampaignCreative(Base):
    """Creative ad variations generated for campaign execution."""
    __tablename__ = "campaign_creatives"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_text: Mapped[str] = mapped_column(Text, nullable=False)
    description_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cta_text: Mapped[str] = mapped_column(String(50), default="Shop Now", nullable=False)
    media_url: Mapped[str] = mapped_column(Text, nullable=False)
    destination_url: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[str] = mapped_column(String(50), default="feed_image", nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="creatives")


class ExternalCampaign(Base):
    """External deployment of a campaign to an ad network."""
    __tablename__ = "external_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ad_account_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), default="meta_ads", nullable=False)
    remote_campaign_id: Mapped[str] = mapped_column(String(255), nullable=False)
    remote_status: Mapped[str] = mapped_column(String(50), nullable=False)
    last_synced_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="external_deployments")
    daily_metrics: Mapped[List["CampaignMetricsDaily"]] = relationship(
        "CampaignMetricsDaily", back_populates="external_campaign", cascade="all, delete-orphan"
    )


class CampaignMetricsDaily(Base):
    """Daily performance analytics aggregated from ad platform."""
    __tablename__ = "campaign_metrics_daily"
    __table_args__ = (
        UniqueConstraint("external_campaign_id", "date", name="uq_campaign_metrics_daily"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    external_campaign_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("external_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    spend: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reach: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    conversions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversion_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    synced_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    external_campaign: Mapped["ExternalCampaign"] = relationship("ExternalCampaign", back_populates="daily_metrics")


import datetime
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class ContentGeneration(Base, TimestampMixin):
    """AI Studio generation session for a product."""
    __tablename__ = "content_generations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # shopify_copy, instagram_caption, ad_hook
    target_channel: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="gemini-3.8-flash", nullable=False)
    prompt_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    token_count_input: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count_output: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    versions: Mapped[List["ContentVersion"]] = relationship(
        "ContentVersion", back_populates="generation", cascade="all, delete-orphan"
    )
    assets: Mapped[List["ContentAsset"]] = relationship(
        "ContentAsset", back_populates="generation", cascade="all, delete-orphan"
    )


class ContentVersion(Base, TimestampMixin):
    """Specific revision or variant produced by AI Studio."""
    __tablename__ = "content_versions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    generation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("content_generations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    generated_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    edited_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    generation: Mapped["ContentGeneration"] = relationship("ContentGeneration", back_populates="versions")


class ContentAsset(Base, TimestampMixin):
    """Supporting creative assets (images, banners) linked to content generation."""
    __tablename__ = "content_assets"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    generation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("content_generations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_url: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)

    generation: Mapped["ContentGeneration"] = relationship("ContentGeneration", back_populates="assets")


class SocialPost(Base, TimestampMixin):
    """Scheduled or published social media post."""
    __tablename__ = "social_posts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_connection_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("channel_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("content_versions.id", ondelete="SET NULL"), nullable=True
    )
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)


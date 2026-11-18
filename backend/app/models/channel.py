import datetime
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class ChannelConnection(Base, TimestampMixin):
    """Authorized external sales/marketing channels (Shopify, Meta)."""
    __tablename__ = "channel_connections"
    __table_args__ = (
        UniqueConstraint("organization_id", "channel_type", "account_identifier", name="uq_chan_conn"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)  # shopify, instagram, amazon, flipkart, zepto, ajio
    channel_group: Mapped[str] = mapped_column(String(50), default="storefront", nullable=False, index=True)  # storefront, marketplace, social, quick_commerce
    partner_status: Mapped[str] = mapped_column(String(50), default="connected", nullable=False)  # connected, not_connected, partner_access_required, coming_soon
    account_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    granted_scopes: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    last_synced_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    listings: Mapped[List["ChannelListing"]] = relationship(
        "ChannelListing", back_populates="connection", cascade="all, delete-orphan"
    )
    jobs: Mapped[List["PublishingJob"]] = relationship(
        "PublishingJob", back_populates="connection", cascade="all, delete-orphan"
    )


class ChannelListing(Base):
    """Remote listing state on connected sales channel."""
    __tablename__ = "channel_listings"
    __table_args__ = (
        UniqueConstraint("channel_connection_id", "remote_product_id", name="uq_chan_listing"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_connection_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("channel_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    remote_product_id: Mapped[str] = mapped_column(String(255), nullable=False)
    remote_variant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_sku: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    channel_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    channel_price: Mapped[Optional[float]] = mapped_column(nullable=True)
    channel_attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=True)
    remote_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remote_status: Mapped[str] = mapped_column(String(50), default="published", nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_published_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    connection: Mapped["ChannelConnection"] = relationship("ChannelConnection", back_populates="listings")


class PublishingBatch(Base, TimestampMixin):
    """Multi-channel publishing batch with immutable approval snapshot."""
    __tablename__ = "publishing_batches"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="approved", nullable=False, index=True)
    channels: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    approved_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    approval_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    approval_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    jobs: Mapped[List["PublishingJob"]] = relationship(
        "PublishingJob", back_populates="batch", cascade="all, delete-orphan"
    )


class PublishingJob(Base, TimestampMixin):
    """Asynchronous omnichannel publishing task queue item."""
    __tablename__ = "publishing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_connection_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("channel_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("publishing_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)  # create_listing, update_listing, sync_inventory
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True, nullable=False)
    payload_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scheduled_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    connection: Mapped["ChannelConnection"] = relationship("ChannelConnection", back_populates="jobs")
    batch: Mapped[Optional["PublishingBatch"]] = relationship("PublishingBatch", back_populates="jobs")
    attempts: Mapped[List["PublishingAttempt"]] = relationship(
        "PublishingAttempt", back_populates="job", cascade="all, delete-orphan"
    )


class PublishingAttempt(Base):
    """Log entry of external API publishing attempts for debugging and retry analysis."""
    __tablename__ = "publishing_attempts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("publishing_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped["PublishingJob"] = relationship("PublishingJob", back_populates="attempts")


class WebhookEvent(Base):
    """Inbound webhook idempotency and audit log."""
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("source", "event_id", name="uq_webhook_source_event"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # shopify, meta, razorpay
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="received", nullable=False)
    processed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


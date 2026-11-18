import datetime
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class ChannelOrder(Base, TimestampMixin):
    """Central unified order record retrieved from connected sales channels."""
    __tablename__ = "channel_orders"
    __table_args__ = (
        UniqueConstraint("channel_connection_id", "remote_order_id", name="uq_chan_order_remote"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_connection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("channel_connections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # shopify, woocommerce, amazon, flipkart
    remote_order_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    order_number: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    shipping_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    refund_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    financial_status: Mapped[str] = mapped_column(String(50), default="paid", nullable=False, index=True)  # paid, pending, refunded, voided
    fulfillment_status: Mapped[str] = mapped_column(String(50), default="unfulfilled", nullable=False, index=True)  # unfulfilled, fulfilled, partial, cancelled
    order_lifecycle_status: Mapped[str] = mapped_column(String(50), default="new", nullable=False, index=True)  # new, pending_payment, paid, processing, ready_to_ship, shipped, delivered, cancelled, partially_refunded, refunded, return_requested, returned, payment_failed, on_hold
    order_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    shipping_address: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    billing_address: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_external_update_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inventory_synced: Mapped[bool] = mapped_column(default=False, nullable=False)
    sync_status: Mapped[str] = mapped_column(String(50), default="synced", nullable=False)  # synced, failed, pending
    sync_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    items: Mapped[List["ChannelOrderItem"]] = relationship(
        "ChannelOrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    returns: Mapped[List["ReturnRequest"]] = relationship(
        "ReturnRequest", back_populates="order", cascade="all, delete-orphan"
    )


class ReturnRequest(Base, TimestampMixin):
    """Tracks physical return requests, inspection lifecycles, and warehouse disposition."""
    __tablename__ = "return_requests"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("channel_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    return_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="requested", nullable=False, index=True
    )  # requested -> authorized -> in_transit -> received -> inspected -> completed / rejected / cancelled
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    authorized_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    received_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    inspected_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_refund_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order: Mapped["ChannelOrder"] = relationship("ChannelOrder", back_populates="returns")
    items: Mapped[List["ReturnItem"]] = relationship(
        "ReturnItem", back_populates="return_request", cascade="all, delete-orphan"
    )


class ReturnItem(Base, TimestampMixin):
    """Line items for a physical return with resalable vs damaged inspection disposition."""
    __tablename__ = "return_items"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    return_request_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("return_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("channel_order_items.id", ondelete="SET NULL"), nullable=True
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    product_variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity_ordered: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quantity_previously_returned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_requested: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quantity_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inspection_result: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, pass, partial, damaged
    resalable_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    damaged_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    refund_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    restocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    return_request: Mapped["ReturnRequest"] = relationship("ReturnRequest", back_populates="items")
    order_item: Mapped[Optional["ChannelOrderItem"]] = relationship("ChannelOrderItem")


class ChannelOrderItem(Base):
    """Line items belonging to a channel order."""
    __tablename__ = "channel_order_items"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("channel_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    external_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_product_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_variant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), default=0.0, nullable=True)
    returned_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mapping_status: Mapped[str] = mapped_column(String(30), default="mapped", nullable=False)  # mapped, unmapped, manual_override

    order: Mapped["ChannelOrder"] = relationship("ChannelOrder", back_populates="items")

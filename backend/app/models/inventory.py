"""Unified Inventory & Auditable Stock Movement Ledger Models."""

import datetime
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class StockLevel(Base, TimestampMixin):
    """Current stock distribution across physical locations and inventory states."""
    __tablename__ = "stock_levels"
    __table_args__ = (
        UniqueConstraint("organization_id", "product_variant_id", "location_id", name="uq_stock_loc_variant"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(String(100), default="primary_warehouse", nullable=False)
    
    physical_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_to_sell: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    committed_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    damaged_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    returned_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    def __repr__(self) -> str:
        return f"<StockLevel(sku={self.sku}, available={self.available_to_sell}, physical={self.physical_stock})>"


class InventoryLedger(Base, TimestampMixin):
    """Immutable auditable movement ledger tracking every stock mutation."""
    __tablename__ = "inventory_ledger"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(String(100), default="primary_warehouse", nullable=False)
    
    # Movement types: initial_stock, order_reservation, order_fulfillment, cancellation_release,
    # customer_return, manual_adjustment, stock_transfer, channel_reconciliation, damaged_stock, restock
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Source context: order, return, manual, webhook, reconciliation
    source_type: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<InventoryLedger(sku={self.sku}, type={self.movement_type}, change={self.quantity_change})>"

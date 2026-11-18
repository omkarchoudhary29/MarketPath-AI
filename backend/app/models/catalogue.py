import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import CheckConstraint, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.channel import ChannelListing


class Product(Base, TimestampMixin):
    """The master product catalogue record — immutable single source of truth for the seller."""
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_product_org_sku"),
        CheckConstraint("status IN ('draft', 'active', 'archived')", name="chk_product_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brand_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("brand_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    long_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False, index=True)
    base_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    compare_at_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    cost_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dimensions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    weight: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    materials: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    seo_title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Revision V2 Category Attributes & Compliance Specs
    category_attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    packaging_specs: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    shipping_specs: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    moq: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    compliance_certificates: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    variants: Mapped[List["ProductVariant"]] = relationship(
        "ProductVariant", back_populates="product", cascade="all, delete-orphan"
    )
    media: Mapped[List["ProductMedia"]] = relationship(
        "ProductMedia", back_populates="product", cascade="all, delete-orphan", order_by="ProductMedia.display_order"
    )
    overrides: Mapped[List["ProductChannelOverride"]] = relationship(
        "ProductChannelOverride", back_populates="product", cascade="all, delete-orphan"
    )
    listings: Mapped[List["ChannelListing"]] = relationship(
        "ChannelListing", backref="product", cascade="all, delete-orphan"
    )


class ProductVariant(Base, TimestampMixin):
    """Product SKU variant (size, color, material variations)."""
    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    options: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="variants")


class ProductMedia(Base, TimestampMixin):
    """Product visual assets hosted on Cloudinary."""
    __tablename__ = "product_media"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=False)
    media_url: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str] = mapped_column(String(30), default="image", nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="media")


class ProductChannelOverride(Base, TimestampMixin):
    """Channel-specific customisations without modifying the master product."""
    __tablename__ = "product_channel_overrides"
    __table_args__ = (
        UniqueConstraint("product_id", "channel_type", name="uq_prod_channel_override"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)  # shopify, instagram, amazon, flipkart
    custom_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    custom_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    custom_tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    category_mapping: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_approved_for_channel: Mapped[bool] = mapped_column(default=False, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="overrides")

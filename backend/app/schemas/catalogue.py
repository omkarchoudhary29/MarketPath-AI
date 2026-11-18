import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Product Variants ---

class ProductVariantBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=150)
    price: float = Field(..., ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    options: Dict[str, Any] = Field(default_factory=dict)


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    price: Optional[float] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    options: Optional[Dict[str, Any]] = None


class ProductVariantRead(ProductVariantBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime


# --- Product Media ---

class ProductMediaBase(BaseModel):
    cloudinary_public_id: str = Field(..., min_length=1, max_length=255)
    media_url: str = Field(..., min_length=1)
    media_type: str = Field(default="image", max_length=30)
    alt_text: Optional[str] = Field(None, max_length=255)
    display_order: int = Field(default=0, ge=0)


class ProductMediaCreate(ProductMediaBase):
    pass


class ProductMediaReorderItem(BaseModel):
    media_id: uuid.UUID
    display_order: int = Field(..., ge=0)


class ProductMediaReorderRequest(BaseModel):
    items: List[ProductMediaReorderItem]


class ProductMediaRead(ProductMediaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime


# --- Product Channel Overrides ---

class ProductChannelOverrideBase(BaseModel):
    channel_type: str = Field(..., min_length=1, max_length=50)  # shopify, instagram
    custom_title: Optional[str] = Field(None, max_length=255)
    custom_description: Optional[str] = None
    custom_price: Optional[float] = Field(None, ge=0)
    custom_tags: List[str] = Field(default_factory=list)
    category_mapping: Optional[str] = Field(None, max_length=255)
    is_approved_for_channel: bool = False


class ProductChannelOverrideCreate(ProductChannelOverrideBase):
    pass


class ProductChannelOverrideRead(ProductChannelOverrideBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    updated_at: datetime.datetime


# --- Master Product ---

class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=100)
    status: str = Field(default="draft", pattern=r"^(draft|active|archived)$")
    base_price: float = Field(..., ge=0)
    compare_at_price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    stock_quantity: int = Field(default=0, ge=0)
    dimensions: Dict[str, Any] = Field(default_factory=dict)
    weight: Optional[float] = Field(None, ge=0)
    materials: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    seo_title: Optional[str] = Field(None, max_length=150)
    seo_description: Optional[str] = None
    brand_profile_id: Optional[uuid.UUID] = None
    # Revision V2 Category Specs & Packaging
    category_attributes: Dict[str, Any] = Field(default_factory=dict)
    packaging_specs: Dict[str, Any] = Field(default_factory=dict)
    shipping_specs: Dict[str, Any] = Field(default_factory=dict)
    moq: int = Field(default=1, ge=1)
    compliance_certificates: List[str] = Field(default_factory=list)


class ProductCreate(ProductBase):
    variants: List[ProductVariantCreate] = Field(default_factory=list)
    media: List[ProductMediaCreate] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = Field(None, pattern=r"^(draft|active|archived)$")
    base_price: Optional[float] = Field(None, ge=0)
    compare_at_price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    stock_quantity: Optional[int] = Field(None, ge=0)
    dimensions: Optional[Dict[str, Any]] = None
    weight: Optional[float] = Field(None, ge=0)
    materials: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    seo_title: Optional[str] = Field(None, max_length=150)
    seo_description: Optional[str] = None
    brand_profile_id: Optional[uuid.UUID] = None
    category_attributes: Optional[Dict[str, Any]] = None
    packaging_specs: Optional[Dict[str, Any]] = None
    shipping_specs: Optional[Dict[str, Any]] = None
    moq: Optional[int] = Field(None, ge=1)
    compliance_certificates: Optional[List[str]] = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    primary_image_url: Optional[str] = None
    variants_count: int = 0


class ProductDetailRead(ProductRead):
    variants: List[ProductVariantRead] = Field(default_factory=list)
    media: List[ProductMediaRead] = Field(default_factory=list)
    overrides: List[ProductChannelOverrideRead] = Field(default_factory=list)


class ProductListResponse(BaseModel):
    items: List[ProductRead]
    total: int
    page: int
    page_size: int
    total_pages: int


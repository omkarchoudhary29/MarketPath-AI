import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PublishAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    attempt_number: int
    http_status: Optional[int] = None
    error_message: Optional[str] = None
    attempted_at: datetime.datetime


class PublishJobCreate(BaseModel):
    product_id: uuid.UUID
    channel_connection_id: uuid.UUID
    job_type: str = Field(default="create_listing", pattern=r"^(create_listing|update_listing|sync_inventory|publish_post)$")
    idempotency_key: Optional[str] = None
    scheduled_at: Optional[datetime.datetime] = None


class PublishJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    product_id: uuid.UUID
    channel_connection_id: uuid.UUID
    channel_type: str
    account_name: str
    product_title: str
    product_sku: str
    idempotency_key: str
    job_type: str
    status: str  # queued, processing, published, failed, action_required
    payload_snapshot: Dict[str, Any]
    retry_count: int
    scheduled_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    attempts: List[PublishAttemptRead] = Field(default_factory=list)
    remote_product_id: Optional[str] = None
    remote_url: Optional[str] = None
    error_summary: Optional[str] = None


class PublishPreviewRequest(BaseModel):
    product_id: uuid.UUID
    channel_type: str = Field(..., pattern=r"^(shopify|instagram|woocommerce|amazon|flipkart|google_merchant)$")


class PublishPreviewResponse(BaseModel):
    product_id: uuid.UUID
    channel_type: str
    payload_preview: Dict[str, Any]
    validation_passed: bool
    validation_warnings: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    master_source: Dict[str, Any]
    overrides_applied: bool


class BatchPreviewRequest(BaseModel):
    product_id: uuid.UUID
    channel_types: List[str] = Field(default_factory=lambda: ["shopify", "woocommerce", "amazon", "flipkart"])


class BatchPreviewResponse(BaseModel):
    product_id: str
    product_title: str
    product_sku: str
    channels: List[str]
    overall_valid: bool
    approval_hash: str
    channel_previews: Dict[str, Any]


class PublishBatchCreate(BaseModel):
    product_id: uuid.UUID
    channel_connection_ids: List[uuid.UUID]
    approval_hash: str
    notes: Optional[str] = None


class PublishBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    product_id: uuid.UUID
    status: str  # approved, processing, completed, partially_completed, failed
    channels: List[str]
    approved_by_user_id: Optional[uuid.UUID] = None
    approved_at: datetime.datetime
    approval_hash: str
    approval_snapshot: Dict[str, Any]
    notes: Optional[str] = None
    created_at: datetime.datetime
    jobs: List[PublishJobRead] = Field(default_factory=list)


class ChannelListingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    product_title: str
    product_sku: str
    channel_connection_id: uuid.UUID
    channel_type: str
    account_name: str
    remote_product_id: str
    remote_url: Optional[str] = None
    remote_status: str
    last_published_at: datetime.datetime
    price: float = 0.0
    stock_quantity: int = 0
    external_sku: Optional[str] = None
    channel_title: Optional[str] = None
    channel_price: Optional[float] = None
    last_error: Optional[str] = None


class WebhookIngestResponse(BaseModel):
    status: str
    event_id: str
    source: str
    processed: bool
    message: Optional[str] = None


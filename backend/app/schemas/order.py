import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    product_variant_id: Optional[uuid.UUID] = None
    sku: str
    external_sku: Optional[str] = None
    title: str
    quantity: int
    unit_price: float
    total_price: float
    discount_amount: float = 0.0
    tax_amount: Optional[float] = 0.0
    returned_quantity: int = 0
    mapping_status: str = "mapped"


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    channel_connection_id: Optional[uuid.UUID] = None
    channel_type: str
    remote_order_id: str
    order_number: str
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    total_amount: float
    subtotal: float = 0.0
    discount_amount: float = 0.0
    shipping_amount: float = 0.0
    tax_amount: float = 0.0
    refund_amount: float = 0.0
    currency: str
    financial_status: str
    fulfillment_status: str
    order_lifecycle_status: str = "new"
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    cancellation_reason: Optional[str] = None
    shipping_address: Dict[str, Any] = {}
    order_date: datetime.datetime
    inventory_synced: bool
    sync_status: str
    sync_notes: Optional[str] = None
    created_at: datetime.datetime
    items: List[OrderItemRead] = []


class OrderListResponse(BaseModel):
    total_orders: int
    total_revenue_inr: float
    orders: List[OrderRead]


class OrderSyncRequest(BaseModel):
    channel_type: Optional[str] = None  # None for all connected channels


class OrderSyncResponse(BaseModel):
    synced_channels: List[str]
    orders_ingested: int
    inventory_updates_queued: int
    notes: List[str]


class OrderFulfillRequest(BaseModel):
    carrier: str
    tracking_number: str
    tracking_url: Optional[str] = None


class OrderCancelRequest(BaseModel):
    reason: Optional[str] = None


class OrderRefundRequest(BaseModel):
    refund_amount: float
    restock_items: bool = False
    reason: Optional[str] = None

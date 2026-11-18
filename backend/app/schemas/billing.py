import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PlanBase(BaseModel):
    name: str = Field(..., max_length=50)
    monthly_price_inr: int = Field(..., ge=0)
    max_active_skus: int = Field(..., ge=1)
    max_connected_channels: int = Field(..., ge=1)
    ai_generation_monthly_quota: int = Field(..., ge=0)
    description: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    is_active: bool = True


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    monthly_price_inr: Optional[int] = None
    max_active_skus: Optional[int] = None
    max_connected_channels: Optional[int] = None
    ai_generation_monthly_quota: Optional[int] = None
    description: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class PlanRead(PlanBase):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class SubscriptionRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    plan_id: uuid.UUID
    status: str
    current_period_start: datetime.datetime
    current_period_end: datetime.datetime
    cancel_at_period_end: bool
    gateway_subscription_id: Optional[str] = None
    plan: PlanRead
    model_config = ConfigDict(from_attributes=True)


class UsageMeterItem(BaseModel):
    metric: str
    label: str
    used: int
    limit: int
    percentage: float
    unit: str = "units"


class UsageStatsRead(BaseModel):
    organization_id: uuid.UUID
    plan_name: str
    period_start: datetime.datetime
    period_end: datetime.datetime
    active_skus: UsageMeterItem
    connected_channels: UsageMeterItem
    ai_generations: UsageMeterItem
    publishing_jobs: UsageMeterItem
    team_members: UsageMeterItem


class CheckoutRequest(BaseModel):
    plan_id: uuid.UUID
    gateway: str = Field("razorpay", description="Payment provider: razorpay or cashfree")


class CheckoutResponse(BaseModel):
    order_id: str
    amount_inr: float
    currency: str = "INR"
    key_id: str
    gateway: str
    plan_name: str
    organization_id: uuid.UUID


class PaymentVerifyRequest(BaseModel):
    gateway: str = Field(..., description="razorpay or cashfree")
    order_id: str
    payment_id: str
    signature: str
    plan_id: Optional[uuid.UUID] = None


class PaymentRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    amount_inr: float
    currency: str
    gateway: str
    gateway_payment_id: str
    gateway_order_id: Optional[str] = None
    status: str
    receipt_url: Optional[str] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class ServiceCatalogItem(BaseModel):
    id: str
    service_type: str
    name: str
    short_description: str
    scope_bullets: List[str]
    starting_price_inr: int
    deliverable_timeline: str
    recommended_for: str


class ServiceOrderCreate(BaseModel):
    service_type: str = Field(..., max_length=100)
    scope_description: str = Field(..., min_length=10)
    target_budget_inr: Optional[int] = Field(None, ge=500)
    requirements: Optional[Dict[str, Any]] = None
    due_date: Optional[datetime.date] = None


class ServiceOrderUpdate(BaseModel):
    status: Optional[str] = None
    quoted_price_inr: Optional[int] = None
    assigned_operator_id: Optional[uuid.UUID] = None
    deliverables_notes: Optional[str] = None
    due_date: Optional[datetime.date] = None


class ServiceOrderRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    service_type: str
    scope_description: str
    quoted_price_inr: int
    assigned_operator_id: Optional[uuid.UUID] = None
    status: str
    deliverables_notes: Optional[str] = None
    due_date: Optional[datetime.date] = None
    requirements_json: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

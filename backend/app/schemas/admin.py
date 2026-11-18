import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.billing import PlanRead, ServiceOrderRead


class AdminOverviewTelemetry(BaseModel):
    total_organizations: int
    active_organizations: int
    total_users: int
    total_products: int
    total_publishing_jobs: int
    failed_publishing_jobs: int
    publishing_success_rate: float
    total_revenue_inr: float
    active_paid_subscribers: int
    pending_service_orders: int
    connector_health: Dict[str, Any]
    operator_email: str
    telemetry: Optional[Dict[str, Any]] = None


class AdminOrgRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    plan_name: str
    subscription_status: str
    products_count: int
    channels_count: int
    members_count: int
    created_at: datetime.datetime


class AdminOrgStatusUpdate(BaseModel):
    is_active: bool
    reason: Optional[str] = None


class AdminUserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    account_type: Optional[str] = "company"
    is_platform_admin: bool
    is_active: bool = True
    vetting_status: str = "approved"
    memberships_count: int
    created_at: datetime.datetime


class AdminUserAdminStatusUpdate(BaseModel):
    is_platform_admin: bool


class AdminJobRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    organization_name: str
    product_title: str
    channel_type: str
    job_type: str
    status: str
    retry_count: int
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None


class AdminJobRetryResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    message: str


class AdminServiceOrderUpdate(BaseModel):
    status: Optional[str] = None
    quoted_price_inr: Optional[int] = None
    assigned_operator_id: Optional[uuid.UUID] = None
    deliverables_notes: Optional[str] = None
    due_date: Optional[datetime.date] = None

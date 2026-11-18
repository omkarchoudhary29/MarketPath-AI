import datetime
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class Plan(Base, TimestampMixin):
    """SaaS pricing tier (Starter, Growth, Scale)."""
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    monthly_price_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    max_active_skus: Mapped[int] = mapped_column(Integer, nullable=False)
    max_connected_channels: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_generation_monthly_quota: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    features: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Subscription(Base, TimestampMixin):
    """Tenant subscription instance."""
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("plans.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    current_period_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gateway_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gateway_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    plan: Mapped["Plan"] = relationship("Plan")


class UsageEvent(Base):
    """Usage metering records for quotas (AI generations, publishing runs)."""
    __tablename__ = "usage_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ai_tokens, published_product, ad_brief
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Payment(Base):
    """Payment transaction records from payment gateways."""
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_inr: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    gateway: Mapped[str] = mapped_column(String(50), nullable=False)  # razorpay, cashfree
    gateway_payment_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    gateway_order_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # pending, success, failed, refunded
    receipt_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ServiceOrder(Base, TimestampMixin):
    """Managed service requests (assisted onboarding, catalogue setup)."""
    __tablename__ = "service_orders"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_type: Mapped[str] = mapped_column(String(100), nullable=False)
    scope_description: Mapped[str] = mapped_column(Text, nullable=False)
    quoted_price_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    assigned_operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="requested", nullable=False)
    deliverables_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    requirements_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


import datetime
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class ConsultationRequest(Base, TimestampMixin):
    """Inbound high-touch growth consultation & bespoke onboarding inquiries."""
    __tablename__ = "consultation_requests"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    reference_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    brand_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    business_stage: Mapped[str] = mapped_column(String(50), nullable=False)  # Early Stage (<₹5L/mo), Scaling (₹5L-₹25L/mo), Mature (>₹25L/mo)
    monthly_revenue: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    challenges: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    preferred_time_slot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
    
    # Operational Lifecycle & Assignment
    # submitted -> pending_assignment -> assigned -> awaiting_confirmation -> confirmed -> completed / cancelled / rescheduled / no_show
    status: Mapped[str] = mapped_column(String(50), default="submitted", nullable=False, index=True)
    assigned_consultant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_consultant_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    scheduled_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Diagnostic & Reporting Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Private internal diagnosis
    report_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Shared with client
    recommendations: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    action_items: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reliability, Delivery Status & Concurrency
    email_delivery_status: Mapped[str] = mapped_column(String(50), default="unconfigured_provider", nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<ConsultationRequest(id={self.id}, ref={self.reference_code}, brand={self.brand_name}, status={self.status})>"


class ConsultationAvailabilityRule(Base, TimestampMixin):
    """Availability rule or date block for consultation booking."""
    __tablename__ = "consultation_availability_rules"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    rule_type: Mapped[str] = mapped_column(String(50), default="blocked_date", nullable=False)  # blocked_date, custom_slot, holiday
    specific_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True, index=True)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0=Monday, 6=Sunday
    start_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "10:00"
    end_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "18:00"
    slot_capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<ConsultationAvailabilityRule(id={self.id}, type={self.rule_type}, date={self.specific_date})>"

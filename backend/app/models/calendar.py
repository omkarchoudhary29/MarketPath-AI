import datetime
import uuid
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin


class BusinessCalendarEvent(Base, TimestampMixin):
    """Operational business calendar events: renewals, campaigns, launches, meetings, tasks."""
    __tablename__ = "business_calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # subscription_renewal, campaign, product_launch, agency_meeting, task, reminder
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # product, campaign, subscription, agency_engagement
    related_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(30), default="#6366F1", nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="scheduled", nullable=False)  # scheduled, completed, cancelled
    external_provider: Mapped[str] = mapped_column(String(50), default="internal", nullable=False)  # internal, google, outlook
    external_calendar_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(50), default="synced", nullable=False)  # synced, pending, failed
    last_synced_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<BusinessCalendarEvent(id={self.id}, title={self.title}, type={self.event_type})>"


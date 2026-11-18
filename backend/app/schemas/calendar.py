import datetime
import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BusinessCalendarEventBase(BaseModel):
    event_type: str = Field(..., description="subscription_renewal, campaign, product_launch, agency_meeting, channel_sync, task")
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None
    is_all_day: bool = False
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[uuid.UUID] = None
    color: Optional[str] = "#6366F1"
    status: str = Field(default="scheduled", pattern=r"^(scheduled|completed|cancelled)$")


class BusinessCalendarEventCreate(BusinessCalendarEventBase):
    pass


class BusinessCalendarEventUpdate(BaseModel):
    event_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    is_all_day: Optional[bool] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[uuid.UUID] = None
    color: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(scheduled|completed|cancelled)$")


class BusinessCalendarEventRead(BusinessCalendarEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    external_provider: str = "internal"
    external_calendar_id: Optional[str] = None
    external_event_id: Optional[str] = None
    sync_status: str = "synced"
    last_synced_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CalendarConnectRequest(BaseModel):
    provider: str = Field(..., pattern=r"^(google|outlook)$")
    auth_code: Optional[str] = None
    calendar_id: Optional[str] = None


class CalendarSyncResponse(BaseModel):
    provider: str
    connected: bool
    status: str
    events_synced: int
    message: str


class CalendarEventsListResponse(BaseModel):
    items: List[BusinessCalendarEventRead]
    total: int


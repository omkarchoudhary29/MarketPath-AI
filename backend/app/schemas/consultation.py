import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ConsultationCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    brand_name: str = Field(..., min_length=2, max_length=150)
    category: str = Field(..., min_length=2, max_length=100)
    business_stage: str = Field(..., min_length=2, max_length=50)
    monthly_revenue: Optional[str] = Field(None, max_length=50)
    challenges: Optional[str] = None
    preferred_date: Optional[datetime.date] = None
    preferred_time_slot: Optional[str] = Field(None, max_length=100)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)
    idempotency_key: Optional[str] = Field(None, max_length=64)

    @field_validator("preferred_date", mode="before")
    @classmethod
    def coerce_empty_date(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("phone", "challenges", "monthly_revenue", "preferred_time_slot", "idempotency_key", mode="before")
    @classmethod
    def coerce_empty_strings(cls, v):
        if v == "" or v is None:
            return None
        return v


class ConsultationSlotInfo(BaseModel):
    slot: str
    available: bool
    capacity: int = 1
    booked_count: int = 0


class ConsultationAvailabilityResponse(BaseModel):
    date: datetime.date
    timezone: str = "Asia/Kolkata"
    is_available: bool
    reason: Optional[str] = None
    slots: List[ConsultationSlotInfo] = Field(default_factory=list)


class ConsultationAvailabilityRuleCreate(BaseModel):
    rule_type: str = Field(default="blocked_date", max_length=50)
    specific_date: Optional[datetime.date] = None
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    slot_capacity: int = 1
    is_blocked: bool = True
    notes: Optional[str] = None

    @field_validator("specific_date", mode="before")
    @classmethod
    def coerce_empty_rule_date(cls, v):
        if v == "" or v is None:
            return None
        return v


class ConsultationAvailabilityRuleResponse(BaseModel):
    id: uuid.UUID
    rule_type: str
    specific_date: Optional[datetime.date] = None
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    slot_capacity: int = 1
    is_blocked: bool = True
    notes: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    meeting_link: Optional[str] = None


class ConsultationAssign(BaseModel):
    consultant_id: uuid.UUID
    consultant_name: str = Field(..., min_length=2, max_length=150)


class ConsultationConfirm(BaseModel):
    scheduled_at: datetime.datetime
    meeting_link: Optional[str] = None
    duration_minutes: int = 30


class ConsultationReschedule(BaseModel):
    preferred_date: datetime.date
    preferred_time_slot: str = Field(..., min_length=2, max_length=50)
    reason: Optional[str] = None


class ConsultationCancel(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)


class ConsultationReportSubmit(BaseModel):
    internal_notes: Optional[str] = None
    report_summary: str = Field(..., min_length=10)
    recommendations: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)


class ConsultationReportRead(BaseModel):
    id: uuid.UUID
    reference_code: str
    brand_name: str
    category: str
    status: str
    report_summary: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultationResponse(BaseModel):
    id: uuid.UUID
    reference_code: str
    full_name: str
    email: str
    phone: Optional[str] = None
    brand_name: str
    category: str
    business_stage: str
    monthly_revenue: Optional[str] = None
    challenges: Optional[str] = None
    preferred_date: Optional[datetime.date] = None
    preferred_time_slot: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    status: str
    assigned_consultant_id: Optional[uuid.UUID] = None
    assigned_consultant_name: Optional[str] = None
    scheduled_at: Optional[datetime.datetime] = None
    duration_minutes: int = 30
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    report_summary: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    cancellation_reason: Optional[str] = None
    email_delivery_status: str = "unconfigured_provider"
    idempotency_key: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultationAdminStats(BaseModel):
    total_consultations: int
    submitted_count: int
    confirmed_count: int
    completed_count: int
    cancelled_count: int
    status_breakdown: Dict[str, int]

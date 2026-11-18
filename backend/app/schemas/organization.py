import datetime
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Organization or business name")
    slug: Optional[str] = Field(None, min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    brand_name: Optional[str] = Field(None, min_length=2, max_length=150, description="Initial brand profile name")
    category: Optional[str] = Field("Home & Living", description="Primary brand category")
    currency: Optional[str] = Field("INR", min_length=3, max_length=3)
    timezone: Optional[str] = Field("Asia/Kolkata")


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    settings: Optional[Dict[str, Any]] = None


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    settings: Dict[str, Any]
    created_at: datetime.datetime
    updated_at: datetime.datetime


class OrganizationWithRole(OrganizationRead):
    role: str

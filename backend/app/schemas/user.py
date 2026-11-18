import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfileBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    avatar_url: Optional[str] = None


class UserProfileRead(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_type: Optional[str] = "company"
    is_platform_admin: bool
    is_active: bool = True
    must_change_password: bool = False
    mfa_enabled: bool = False
    vetting_status: str = "approved"
    created_at: datetime.datetime
    updated_at: datetime.datetime


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    avatar_url: Optional[str] = None


class UserSyncRequest(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

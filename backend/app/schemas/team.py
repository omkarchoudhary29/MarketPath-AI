import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from backend.app.schemas.user import UserProfileRead


class TeamMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    user: UserProfileRead


class TeamInviteCreate(BaseModel):
    email: EmailStr
    role: str = Field("marketer", pattern=r"^(admin|marketer|viewer)$")
    full_name: Optional[str] = None


class TeamMemberUpdate(BaseModel):
    role: str = Field(..., pattern=r"^(admin|marketer|viewer)$")


class TeamInvitationCreate(BaseModel):
    email: EmailStr
    role: str = Field("marketer", pattern=r"^(admin|marketer|viewer)$")


class TeamInvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    invited_by_user_id: uuid.UUID
    email: str
    role: str
    status: str
    expires_at: datetime.datetime
    created_at: datetime.datetime
    invite_url: Optional[str] = None


class TeamInvitationVerifyResponse(BaseModel):
    email: str
    organization_name: str
    role: str
    is_valid: bool
    expires_at: datetime.datetime


class TeamInvitationAccept(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    password: str = Field(..., min_length=8)

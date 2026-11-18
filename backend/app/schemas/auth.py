import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from backend.app.schemas.organization import OrganizationWithRole
from backend.app.schemas.user import UserProfileRead


class TokenPayload(BaseModel):
    sub: str
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
    is_platform_admin: bool = False


class AuthMeResponse(BaseModel):
    user: UserProfileRead
    organizations: List[OrganizationWithRole]
    active_organization_id: Optional[uuid.UUID] = None


class LoginAccountRequest(BaseModel):
    email: EmailStr
    password: str
    account_type: str = Field("company", pattern=r"^(company|agency|consultant|admin)$")


class LoginAccountResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    account_type: str
    redirect_url: str
    session_id: Optional[uuid.UUID] = None
    user: UserProfileRead
    organization: Optional[OrganizationWithRole] = None


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Successfully logged out. Session invalidated."


class RegisterCompanyRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    founder_name: Optional[str] = Field(None, min_length=2, max_length=150)
    brand_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6)
    category: str = Field(..., min_length=2, max_length=100)
    custom_category: Optional[str] = None
    website: Optional[str] = None
    website_url: Optional[str] = None

    @property
    def resolved_full_name(self) -> str:
        name = self.full_name or self.founder_name
        if not name or len(name.strip()) < 2:
            raise ValueError("Full name / Founder name must be at least 2 characters.")
        return name.strip()

    @property
    def resolved_website(self) -> Optional[str]:
        return (self.website or self.website_url or "").strip() or None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    success: bool = True
    message: str
    reset_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)


class ResetPasswordResponse(BaseModel):
    success: bool = True
    message: str


class RegisterAgencyRequest(BaseModel):
    agency_name: str = Field(..., min_length=2, max_length=150)
    contact_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    website: Optional[str] = None
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    service_categories: List[str] = Field(default_factory=list)
    years_of_experience: int = Field(default=1, ge=0)
    portfolio_url: Optional[str] = None
    description: str = Field(..., min_length=10)
    gst_number: Optional[str] = None


class RegisterConsultantRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    location: str = Field(..., min_length=2, max_length=100)
    professional_title: str = Field(..., min_length=2, max_length=150)
    expertise_categories: List[str] = Field(default_factory=list)
    years_of_experience: int = Field(default=1, ge=0)
    bio: str = Field(..., min_length=10)
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    areas_of_specialization: List[str] = Field(default_factory=list)
    availability: str = Field("part_time", description="full_time, part_time, advisory")


class ApplicationSubmittedResponse(BaseModel):
    success: bool = True
    account_type: str
    status: str = "under_review"
    message: str
    user_id: uuid.UUID


class ChangePasswordRequest(BaseModel):
    old_password: Optional[str] = None
    new_password: str = Field(..., min_length=8)



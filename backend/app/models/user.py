import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.organization import OrganizationMember


class UserProfile(Base, TimestampMixin):
    """Maps to Supabase Auth auth.users record by UUID."""
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    account_type: Mapped[str] = mapped_column(String(50), default="company", nullable=False)  # company, agency, consultant, admin
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vetting_status: Mapped[str] = mapped_column(String(50), default="approved", nullable=False)  # draft, submitted, under_review, approved, rejected
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    memberships: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember", back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        if "role" in kwargs:
            kwargs.setdefault("account_type", kwargs.pop("role"))
        super().__init__(**kwargs)

    @property
    def role(self) -> str:
        """Helper alias matching account_type for RBAC consistency."""
        if self.is_platform_admin:
            return "admin"
        return self.account_type

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, email={self.email}, admin={self.is_platform_admin})>"


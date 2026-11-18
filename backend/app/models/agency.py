import datetime
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.base import GUID, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.organization import Organization
    from backend.app.models.user import UserProfile


class AgencyProfile(Base, TimestampMixin):
    """Business profile for digital marketing, creative, and technical agencies."""
    __tablename__ = "agency_profiles"
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('registered', 'verification_pending', 'under_review', 'verified', 'rejected', 'suspended')",
            name="chk_agency_verification_status",
        ),
        CheckConstraint(
            "remote_or_local IN ('remote', 'local', 'both')",
            name="chk_agency_delivery_mode",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    tagline: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    remote_or_local: Mapped[str] = mapped_column(String(50), nullable=False, default="both")
    team_size: Mapped[str] = mapped_column(String(50), nullable=False, default="1-10")
    founded_year: Mapped[int] = mapped_column(Integer, nullable=False, default=2020)
    category_specialties: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    service_offerings: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    min_budget_inr: Mapped[int] = mapped_column(Integer, nullable=False, default=10000)
    max_budget_inr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gst_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="registered", index=True
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True
    )
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tier: Mapped[str] = mapped_column(String(50), default="standard", nullable=False)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    services: Mapped[List["AgencyService"]] = relationship(
        "AgencyService", back_populates="agency_profile", cascade="all, delete-orphan"
    )
    packages: Mapped[List["AgencyServicePackage"]] = relationship(
        "AgencyServicePackage", back_populates="agency_profile", cascade="all, delete-orphan"
    )
    portfolios: Mapped[List["AgencyPortfolio"]] = relationship(
        "AgencyPortfolio", back_populates="agency_profile", cascade="all, delete-orphan"
    )
    quote_requests: Mapped[List["AgencyQuoteRequest"]] = relationship(
        "AgencyQuoteRequest", back_populates="agency_profile"
    )
    engagements: Mapped[List["AgencyEngagement"]] = relationship(
        "AgencyEngagement", back_populates="agency_profile"
    )
    reviews: Mapped[List["AgencyReview"]] = relationship(
        "AgencyReview", back_populates="agency_profile"
    )

    def __repr__(self) -> str:
        return f"<AgencyProfile(id={self.id}, name={self.name}, status={self.verification_status})>"


class AgencyService(Base, TimestampMixin):
    """Specific capabilities and services offered by an agency."""
    __tablename__ = "agency_services"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agency_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agency_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    deliverables: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    pricing_model: Mapped[str] = mapped_column(String(50), nullable=False, default="monthly_retainer")
    min_price_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    max_price_inr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_duration: Mapped[str] = mapped_column(String(100), nullable=False, default="Ongoing monthly")
    target_industries: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    agency_profile: Mapped["AgencyProfile"] = relationship("AgencyProfile", back_populates="services")
    packages: Mapped[List["AgencyServicePackage"]] = relationship(
        "AgencyServicePackage", back_populates="service"
    )


class AgencyServicePackage(Base, TimestampMixin):
    """Standardized service packages and tiered offerings."""
    __tablename__ = "agency_service_packages"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agency_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agency_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("agency_services.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    package_tier: Mapped[str] = mapped_column(String(50), default="growth", nullable=False)
    price_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_interval: Mapped[str] = mapped_column(String(50), default="monthly", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    deliverables: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    turnaround_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    agency_profile: Mapped["AgencyProfile"] = relationship("AgencyProfile", back_populates="packages")
    service: Mapped[Optional["AgencyService"]] = relationship("AgencyService", back_populates="packages")


class AgencyPortfolio(Base, TimestampMixin):
    """Verified case studies, creative assets, and client track records."""
    __tablename__ = "agency_portfolios"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agency_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agency_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    client_brand_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    project_title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    case_study_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    media_urls: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    is_demo_work: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    agency_profile: Mapped["AgencyProfile"] = relationship("AgencyProfile", back_populates="portfolios")


class SellerAgencyRequirement(Base, TimestampMixin):
    """Saved business requirement profiles and AI search briefs generated by D2C sellers."""
    __tablename__ = "seller_agency_requirements"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brand_name: Mapped[str] = mapped_column(String(150), nullable=False)
    product_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    business_stage: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sales_channels: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    catalogue_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_market: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    business_objectives: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    required_services: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    monthly_budget_inr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    project_budget_inr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_budget_inr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    engagement_duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    preferred_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    remote_or_local: Mapped[str] = mapped_column(String(50), default="both", nullable=False)
    industry_experience_required: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preferred_agency_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expected_start_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    special_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_search_brief: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_suggested_services: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    quote_requests: Mapped[List["AgencyQuoteRequest"]] = relationship(
        "AgencyQuoteRequest", back_populates="requirement"
    )


class AgencyQuoteRequest(Base, TimestampMixin):
    """Structured quotation requests and initial client proposals."""
    __tablename__ = "agency_quote_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'submitted', 'received', 'under_review', 'clarification_required', 'quotation_sent', 'accepted', 'declined', 'engagement_started', 'completed', 'cancelled')",
            name="chk_quote_request_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agency_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agency_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seller_requirement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("seller_agency_requirements.id", ondelete="SET NULL"), nullable=True
    )
    project_title: Mapped[str] = mapped_column(String(200), nullable=False)
    project_description: Mapped[str] = mapped_column(Text, nullable=False)
    budget_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_type: Mapped[str] = mapped_column(String(50), default="monthly", nullable=False)
    timeframe: Mapped[str] = mapped_column(String(100), nullable=False)
    attachment_urls: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    share_contact_consent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sanitized_founder_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="submitted", nullable=False, index=True)
    agency_response_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quotation_amount_inr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quotation_deliverables: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    quotation_valid_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    agency_profile: Mapped["AgencyProfile"] = relationship("AgencyProfile", back_populates="quote_requests")
    requirement: Mapped[Optional["SellerAgencyRequirement"]] = relationship(
        "SellerAgencyRequirement", back_populates="quote_requests"
    )
    engagements: Mapped[List["AgencyEngagement"]] = relationship(
        "AgencyEngagement", back_populates="quote_request"
    )


class AgencyEngagement(Base, TimestampMixin):
    """Ongoing or completed commercial service contract between a seller and an agency."""
    __tablename__ = "agency_engagements"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'in_progress', 'completed', 'cancelled', 'disputed')",
            name="chk_agency_engagement_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    quote_request_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agency_quote_requests.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agency_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agency_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    package_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("agency_service_packages.id", ondelete="SET NULL"), nullable=True
    )
    agreed_price_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_type: Mapped[str] = mapped_column(String(50), default="monthly", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="in_progress", nullable=False, index=True)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    quote_request: Mapped["AgencyQuoteRequest"] = relationship("AgencyQuoteRequest", back_populates="engagements")
    organization: Mapped["Organization"] = relationship("Organization")
    agency_profile: Mapped["AgencyProfile"] = relationship("AgencyProfile", back_populates="engagements")
    package: Mapped[Optional["AgencyServicePackage"]] = relationship("AgencyServicePackage")
    review: Mapped[Optional["AgencyReview"]] = relationship("AgencyReview", back_populates="engagement", uselist=False)


class AgencySavedShortlist(Base):
    """Saves shortlisted agencies for side-by-side comparison and RFP submissions."""
    __tablename__ = "agency_saved_shortlists"
    __table_args__ = (
        UniqueConstraint("organization_id", "agency_profile_id", name="uq_agency_saved_org"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agency_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agency_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    agency_profile: Mapped["AgencyProfile"] = relationship("AgencyProfile")


class AgencyReview(Base):
    """Verified reviews submitted by sellers after completed engagements."""
    __tablename__ = "agency_reviews"
    __table_args__ = (
        UniqueConstraint("engagement_id", name="uq_agency_review_engagement"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_agency_review_rating"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    engagement_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agency_engagements.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agency_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agency_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    # Relationships
    engagement: Mapped["AgencyEngagement"] = relationship("AgencyEngagement", back_populates="review")
    organization: Mapped["Organization"] = relationship("Organization")
    agency_profile: Mapped["AgencyProfile"] = relationship("AgencyProfile", back_populates="reviews")


class AgencyMember(Base):
    """Internal agency team members with agency RBAC roles."""
    __tablename__ = "agency_members"
    __table_args__ = (
        UniqueConstraint("agency_profile_id", "user_id", name="uq_agency_member"),
        CheckConstraint(
            "role IN ('agency_owner', 'agency_admin', 'agency_staff', 'agency_viewer')",
            name="chk_agency_member_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agency_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agency_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="agency_staff")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    agency_profile: Mapped["AgencyProfile"] = relationship("AgencyProfile")
    user: Mapped["UserProfile"] = relationship("UserProfile")


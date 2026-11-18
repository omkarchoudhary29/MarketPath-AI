import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.agency import (
    AgencyEngagement,
    AgencyMember,
    AgencyPortfolio,
    AgencyProfile,
    AgencyQuoteRequest,
    AgencyReview,
    AgencySavedShortlist,
    AgencyService,
    AgencyServicePackage,
    SellerAgencyRequirement,
)
from backend.app.models.audit import AuditLog
from backend.app.models.organization import Organization
from backend.app.models.user import UserProfile
from backend.app.schemas.agency import (
    AgencyEngagementRead,
    AgencyPackageCreate,
    AgencyPackageRead,
    AgencyPortfolioCreate,
    AgencyPortfolioRead,
    AgencyProfileCreate,
    AgencyProfileDetailRead,
    AgencyProfileRead,
    AgencyProfileUpdate,
    AgencyQuotationSubmit,
    AgencyQuoteRequestCreate,
    AgencyQuoteRequestRead,
    AgencyReviewCreate,
    AgencyReviewRead,
    AgencySavedShortlistRead,
    AgencyServiceCreate,
    AgencyServiceRead,
    AgencyVerificationAction,
    SellerRequirementCreate,
    SellerRequirementRead,
    SellerRequirementUpdate,
)

logger = logging.getLogger(__name__)


class AgencyServiceManager:
    """Core domain logic for MarketPath Agency Connect."""

    # -------------------------------------------------------------------------
    # Agency Profile Management
    # -------------------------------------------------------------------------

    @classmethod
    async def register_agency_profile(
        cls,
        db: AsyncSession,
        org_id: uuid.UUID,
        payload: AgencyProfileCreate,
        user_id: uuid.UUID,
    ) -> AgencyProfileRead:
        """Registers a new agency profile in 'registered' status (never auto-verified)."""
        # Ensure slug uniqueness
        existing = await db.execute(select(AgencyProfile).where(AgencyProfile.slug == payload.slug))
        if existing.scalar_one_or_none():
            payload.slug = f"{payload.slug}-{str(uuid.uuid4())[:6]}"

        profile = AgencyProfile(
            organization_id=org_id,
            name=payload.name,
            slug=payload.slug,
            tagline=payload.tagline,
            description=payload.description,
            logo_url=payload.logo_url,
            website=payload.website,
            email=payload.email,
            phone=payload.phone,
            city=payload.city,
            state=payload.state,
            country=payload.country,
            remote_or_local=payload.remote_or_local,
            team_size=payload.team_size,
            founded_year=payload.founded_year,
            category_specialties=payload.category_specialties,
            service_offerings=payload.service_offerings,
            min_budget_inr=payload.min_budget_inr,
            max_budget_inr=payload.max_budget_inr,
            gst_number=payload.gst_number,
            verification_status="registered",
            is_available=payload.is_available,
            is_active=True,
            is_featured=False,
            is_demo=False,
            tier="standard",
            rating_avg=0.0,
            reviews_count=0,
        )
        db.add(profile)
        db.add(
            AuditLog(
                organization_id=org_id,
                actor_user_id=user_id,
                action="agency.registered",
                resource_type="agency_profile",
                resource_id=str(profile.id),
                metadata_json={"name": payload.name, "city": payload.city},
            )
        )
        await db.commit()
        await db.refresh(profile)
        return AgencyProfileRead.model_validate(profile)

    @classmethod
    async def get_agency_by_slug(
        cls, db: AsyncSession, slug: str
    ) -> Optional[AgencyProfileDetailRead]:
        """Fetches an agency with all its services, packages, and portfolios."""
        stmt = (
            select(AgencyProfile)
            .options(
                selectinload(AgencyProfile.services),
                selectinload(AgencyProfile.packages),
                selectinload(AgencyProfile.portfolios),
            )
            .where(AgencyProfile.slug == slug, AgencyProfile.is_active.is_(True))
        )
        res = await db.execute(stmt)
        agency = res.scalar_one_or_none()
        if not agency:
            return None
        return AgencyProfileDetailRead.model_validate(agency)

    @classmethod
    async def list_agencies_for_discovery(
        cls,
        db: AsyncSession,
        search: Optional[str] = None,
        category: Optional[str] = None,
        service: Optional[str] = None,
        location: Optional[str] = None,
        max_budget: Optional[int] = None,
        remote_only: bool = False,
        verification_status: Optional[str] = None,
    ) -> List[AgencyProfileRead]:
        """Discovers agencies using multifaceted search and deterministic filters."""
        stmt = select(AgencyProfile).where(AgencyProfile.is_active.is_(True))

        if verification_status:
            stmt = stmt.where(AgencyProfile.verification_status == verification_status)
        else:
            # By default exclude rejected/suspended
            stmt = stmt.where(AgencyProfile.verification_status.notin_(["rejected", "suspended"]))

        if location:
            stmt = stmt.where(
                func.lower(AgencyProfile.city).contains(location.lower())
                | func.lower(AgencyProfile.state).contains(location.lower())
            )

        if max_budget:
            stmt = stmt.where(AgencyProfile.min_budget_inr <= max_budget)

        if remote_only:
            stmt = stmt.where(AgencyProfile.remote_or_local.in_(["remote", "both"]))

        res = await db.execute(stmt.order_by(AgencyProfile.is_featured.desc(), AgencyProfile.rating_avg.desc()))
        agencies = res.scalars().all()

        filtered = []
        for a in agencies:
            # Client-side / JSON in-memory filtering for SQLite JSON arrays
            if search:
                s_lower = search.lower()
                matches_search = (
                    s_lower in a.name.lower()
                    or s_lower in a.tagline.lower()
                    or s_lower in a.description.lower()
                    or s_lower in a.city.lower()
                )
                if not matches_search:
                    continue

            if category:
                cat_lower = category.lower()
                if not any(cat_lower in c.lower() for c in a.category_specialties):
                    continue

            if service:
                srv_lower = service.lower()
                if not any(srv_lower in s.lower() for s in a.service_offerings):
                    continue

            filtered.append(AgencyProfileRead.model_validate(a))

        return filtered

    # -------------------------------------------------------------------------
    # Seller Requirements Management
    # -------------------------------------------------------------------------

    @classmethod
    async def create_or_update_seller_requirement(
        cls,
        db: AsyncSession,
        org_id: uuid.UUID,
        payload: SellerRequirementCreate,
    ) -> SellerRequirementRead:
        """Saves or updates the seller's active agency search requirement."""
        # Find active requirement for org
        res = await db.execute(
            select(SellerAgencyRequirement).where(
                SellerAgencyRequirement.organization_id == org_id,
                SellerAgencyRequirement.is_active.is_(True),
            )
        )
        req = res.scalar_one_or_none()
        if not req:
            req = SellerAgencyRequirement(
                organization_id=org_id,
                brand_name=payload.brand_name,
                product_category=payload.product_category,
                business_stage=payload.business_stage,
                location=payload.location,
                website=payload.website,
                sales_channels=payload.sales_channels,
                catalogue_size=payload.catalogue_size,
                target_market=payload.target_market,
                business_objectives=payload.business_objectives,
                required_services=payload.required_services,
                monthly_budget_inr=payload.monthly_budget_inr,
                project_budget_inr=payload.project_budget_inr,
                total_budget_inr=payload.total_budget_inr,
                currency=payload.currency,
                engagement_duration=payload.engagement_duration,
                preferred_location=payload.preferred_location,
                remote_or_local=payload.remote_or_local,
                industry_experience_required=payload.industry_experience_required,
                preferred_agency_size=payload.preferred_agency_size,
                expected_start_date=payload.expected_start_date,
                special_requirements=payload.special_requirements,
                ai_search_brief=payload.ai_search_brief,
                ai_suggested_services=payload.ai_suggested_services,
                is_active=True,
            )
            db.add(req)
        else:
            # Update fields
            for field, val in payload.model_dump(exclude_unset=True).items():
                setattr(req, field, val)

        await db.commit()
        await db.refresh(req)
        return SellerRequirementRead.model_validate(req)

    @classmethod
    async def get_seller_requirement(
        cls, db: AsyncSession, org_id: uuid.UUID
    ) -> Optional[SellerRequirementRead]:
        """Gets the most recent active requirement for the seller."""
        res = await db.execute(
            select(SellerAgencyRequirement)
            .where(
                SellerAgencyRequirement.organization_id == org_id,
                SellerAgencyRequirement.is_active.is_(True),
            )
            .order_by(SellerAgencyRequirement.updated_at.desc())
        )
        req = res.scalars().first()
        if not req:
            return None
        return SellerRequirementRead.model_validate(req)

    # -------------------------------------------------------------------------
    # Quote Requests & Quotations Lifecycle
    # -------------------------------------------------------------------------

    @classmethod
    async def submit_quote_request(
        cls,
        db: AsyncSession,
        org_id: uuid.UUID,
        payload: AgencyQuoteRequestCreate,
        user_id: uuid.UUID,
    ) -> AgencyQuoteRequestRead:
        """Submits an introduction and RFP quotation request from a seller to an agency."""
        req = AgencyQuoteRequest(
            organization_id=org_id,
            agency_profile_id=payload.agency_profile_id,
            seller_requirement_id=payload.seller_requirement_id,
            project_title=payload.project_title,
            project_description=payload.project_description,
            budget_inr=payload.budget_inr,
            budget_type=payload.budget_type,
            timeframe=payload.timeframe,
            attachment_urls=payload.attachment_urls,
            share_contact_consent=payload.share_contact_consent,
            contact_email=payload.contact_email,
            contact_phone=payload.contact_phone,
            status="submitted",
        )
        db.add(req)
        db.add(
            AuditLog(
                organization_id=org_id,
                actor_user_id=user_id,
                action="agency.quote_requested",
                resource_type="agency_quote_request",
                resource_id=str(req.id),
                metadata_json={"agency_id": str(payload.agency_profile_id), "budget": payload.budget_inr},
            )
        )
        await db.commit()
        await db.refresh(req)
        return AgencyQuoteRequestRead.model_validate(req)

    @classmethod
    async def list_seller_quote_requests(
        cls, db: AsyncSession, org_id: uuid.UUID
    ) -> List[AgencyQuoteRequestRead]:
        """Lists all quotation requests submitted by this seller tenant."""
        stmt = (
            select(AgencyQuoteRequest, AgencyProfile.name.label("agency_name"))
            .join(AgencyProfile, AgencyQuoteRequest.agency_profile_id == AgencyProfile.id)
            .where(AgencyQuoteRequest.organization_id == org_id)
            .order_by(AgencyQuoteRequest.created_at.desc())
        )
        res = await db.execute(stmt)
        results = []
        for req, agency_name in res.all():
            read_item = AgencyQuoteRequestRead.model_validate(req)
            read_item.agency_name = agency_name
            results.append(read_item)
        return results

    @classmethod
    async def list_agency_inbound_requests(
        cls, db: AsyncSession, agency_id: uuid.UUID
    ) -> List[AgencyQuoteRequestRead]:
        """Lists all quotation requests received by this agency."""
        stmt = (
            select(AgencyQuoteRequest, Organization.name.label("seller_org_name"))
            .join(Organization, AgencyQuoteRequest.organization_id == Organization.id)
            .where(AgencyQuoteRequest.agency_profile_id == agency_id)
            .order_by(AgencyQuoteRequest.created_at.desc())
        )
        res = await db.execute(stmt)
        results = []
        for req, seller_name in res.all():
            read_item = AgencyQuoteRequestRead.model_validate(req)
            read_item.seller_org_name = seller_name
            results.append(read_item)
        return results

    @classmethod
    async def agency_respond_to_request(
        cls,
        db: AsyncSession,
        request_id: uuid.UUID,
        agency_id: uuid.UUID,
        payload: AgencyQuotationSubmit,
    ) -> AgencyQuoteRequestRead:
        """Agency submits a structured proposal / quotation to the seller."""
        res = await db.execute(
            select(AgencyQuoteRequest).where(
                AgencyQuoteRequest.id == request_id,
                AgencyQuoteRequest.agency_profile_id == agency_id,
            )
        )
        req = res.scalar_one_or_none()
        if not req:
            raise ValueError("Quote request not found or does not belong to this agency.")

        req.quotation_amount_inr = payload.quotation_amount_inr
        req.quotation_deliverables = payload.quotation_deliverables
        req.agency_response_notes = payload.agency_response_notes
        req.quotation_valid_until = payload.quotation_valid_until
        req.status = "quotation_sent"

        await db.commit()
        await db.refresh(req)
        return AgencyQuoteRequestRead.model_validate(req)

    @classmethod
    async def seller_accept_quotation(
        cls, db: AsyncSession, request_id: uuid.UUID, org_id: uuid.UUID
    ) -> AgencyEngagementRead:
        """Seller accepts a quotation, establishing an active engagement."""
        res = await db.execute(
            select(AgencyQuoteRequest).where(
                AgencyQuoteRequest.id == request_id,
                AgencyQuoteRequest.organization_id == org_id,
            )
        )
        req = res.scalar_one_or_none()
        if not req or req.status != "quotation_sent":
            raise ValueError("Quote request cannot be accepted in its current state.")

        req.status = "accepted"

        # Create active engagement record
        engagement = AgencyEngagement(
            quote_request_id=req.id,
            organization_id=req.organization_id,
            agency_profile_id=req.agency_profile_id,
            agreed_price_inr=req.quotation_amount_inr or req.budget_inr,
            billing_type=req.budget_type,
            status="active",
            started_at=datetime.datetime.now(datetime.timezone.utc),
            notes=req.agency_response_notes,
        )
        db.add(engagement)
        await db.commit()
        await db.refresh(engagement)
        return AgencyEngagementRead.model_validate(engagement)

    # -------------------------------------------------------------------------
    # Saved Agencies Shortlists
    # -------------------------------------------------------------------------

    @classmethod
    async def toggle_save_agency(
        cls, db: AsyncSession, org_id: uuid.UUID, agency_id: uuid.UUID, notes: Optional[str] = None
    ) -> bool:
        """Saves or unsaves an agency to seller bookmarks."""
        res = await db.execute(
            select(AgencySavedShortlist).where(
                AgencySavedShortlist.organization_id == org_id,
                AgencySavedShortlist.agency_profile_id == agency_id,
            )
        )
        existing = res.scalar_one_or_none()
        if existing:
            await db.delete(existing)
            await db.commit()
            return False
        else:
            new_save = AgencySavedShortlist(
                organization_id=org_id,
                agency_profile_id=agency_id,
                notes=notes,
            )
            db.add(new_save)
            await db.commit()
            return True

    @classmethod
    async def list_saved_agencies(
        cls, db: AsyncSession, org_id: uuid.UUID
    ) -> List[AgencyProfileRead]:
        """Lists all shortlisted agencies for this seller organization."""
        stmt = (
            select(AgencyProfile)
            .join(AgencySavedShortlist, AgencyProfile.id == AgencySavedShortlist.agency_profile_id)
            .where(AgencySavedShortlist.organization_id == org_id)
        )
        res = await db.execute(stmt)
        agencies = res.scalars().all()
        return [AgencyProfileRead.model_validate(a) for a in agencies]

    # -------------------------------------------------------------------------
    # Admin Verification Queue
    # -------------------------------------------------------------------------

    @classmethod
    async def admin_set_verification_status(
        cls,
        db: AsyncSession,
        agency_id: uuid.UUID,
        payload: AgencyVerificationAction,
        admin_user_id: uuid.UUID,
    ) -> AgencyProfileRead:
        """Platform Admin approves, rejects, or suspends an agency profile."""
        res = await db.execute(select(AgencyProfile).where(AgencyProfile.id == agency_id))
        agency = res.scalar_one_or_none()
        if not agency:
            raise ValueError("Agency profile not found.")

        agency.verification_status = payload.verification_status
        agency.verification_notes = payload.verification_notes
        if payload.verification_status in ("verified", "approved"):
            agency.verified_at = datetime.datetime.now(datetime.timezone.utc)
            agency.verified_by_user_id = admin_user_id
            agency.is_active = True
            agency.is_available = True
            # Activate member user profiles
            mem_res = await db.execute(select(AgencyMember).where(AgencyMember.agency_profile_id == agency.id))
            for mem in mem_res.scalars().all():
                u = await db.get(UserProfile, mem.user_id)
                if u:
                    u.vetting_status = "approved"
                    u.is_active = True
        elif payload.verification_status == "rejected":
            agency.is_active = False
            agency.is_available = False
            mem_res = await db.execute(select(AgencyMember).where(AgencyMember.agency_profile_id == agency.id))
            for mem in mem_res.scalars().all():
                u = await db.get(UserProfile, mem.user_id)
                if u:
                    u.vetting_status = "rejected"
        if payload.is_featured is not None:
            agency.is_featured = payload.is_featured
        if payload.tier:
            agency.tier = payload.tier

        db.add(
            AuditLog(
                organization_id=agency.organization_id,
                actor_user_id=admin_user_id,
                action="agency.verification_updated",
                resource_type="agency_profile",
                resource_id=str(agency.id),
                metadata_json={
                    "status": payload.verification_status,
                    "notes": payload.verification_notes,
                },
            )
        )
        await db.commit()
        await db.refresh(agency)
        return AgencyProfileRead.model_validate(agency)

    # -------------------------------------------------------------------------
    # Demo Agency Seeding (Clearly Tagged with is_demo=True)
    # -------------------------------------------------------------------------

    @classmethod
    async def seed_demo_agencies_if_empty(cls, db: AsyncSession, default_org_id: uuid.UUID) -> None:
        """Seeds realistic demo agencies so sellers have rich, genuine matches across all categories."""
        demo_agencies_data = [
            {
                "name": "CraftVerve Media",
                "slug": "craftverve-media",
                "tagline": "Performance creative & visual storytelling for artisan and home brands.",
                "description": "CraftVerve is a specialized creative and paid growth agency partnering with home decor, handicrafts, and artisan D2C brands across Western India. We produce authentic studio photoshoots and run ROI-focused Meta advertising.",
                "city": "Pune",
                "state": "Maharashtra",
                "remote_or_local": "both",
                "team_size": "11-50",
                "founded_year": 2021,
                "category_specialties": ["Home & Living", "Handicrafts & Decor", "Artisan Goods", "Kitchen & Dining"],
                "service_offerings": ["Product photography", "Social media management", "Meta Ads management", "Content creation"],
                "min_budget_inr": 12000,
                "max_budget_inr": 60000,
                "gst_number": "27AAACR1234F1Z8",
                "verification_status": "verified",
                "is_featured": True,
                "is_demo": True,
                "rating_avg": 4.9,
                "reviews_count": 8,
                "email": "hello@craftverve.demo.in",
                "website": "https://craftverve.demo.in",
                "services": [
                    {
                        "name": "D2C Product Photoshoot & Reels",
                        "category": "Product photography",
                        "description": "High-contrast studio and lifestyle photography with aesthetic props tailored for Indian home decor.",
                        "deliverables": ["25 edited high-res images", "5 lifestyle reel cuts", "Multi-angle variant crops"],
                        "min_price_inr": 7500,
                        "pricing_model": "project_based",
                    },
                    {
                        "name": "Meta Ads Growth Retainer",
                        "category": "Meta Ads management",
                        "description": "Full-funnel Meta Ads execution, pixel optimization, audience clusters, and ROAS scaling.",
                        "deliverables": ["Campaign setup & testing", "Weekly ad fatigue refreshes", "Custom audience lookalikes", "Bi-weekly reporting"],
                        "min_price_inr": 15000,
                        "pricing_model": "monthly_retainer",
                    },
                ],
                "packages": [
                    {
                        "name": "Artisan Home Decor Sprint",
                        "package_tier": "starter",
                        "price_inr": 12000,
                        "billing_interval": "monthly",
                        "description": "Photoshoot asset generation plus managed Instagram social presence.",
                        "deliverables": ["15 studio photos", "8 social feed posts", "2 reels", "Monthly engagement report"],
                        "turnaround_days": 15,
                    },
                    {
                        "name": "Full D2C Growth Suite",
                        "package_tier": "growth",
                        "price_inr": 22000,
                        "billing_interval": "monthly",
                        "description": "Complete product photography, Instagram management, and Meta Ads scaling.",
                        "deliverables": ["30 studio photos", "16 posts & 6 reels", "Active Meta ad management", "Weekly ROAS sync"],
                        "turnaround_days": 30,
                    },
                ],
                "portfolios": [
                    {
                        "client_brand_name": "Aura Terra Living",
                        "category": "Home & Living",
                        "project_title": "Ceramic Planter Hero Launch",
                        "description": "Shot 25 warm earth-toned product images and executed high-intent Instagram carousel ads resulting in 3.6x ROAS.",
                        "key_metrics": {"roas": "3.6x", "cpa": "₹190", "gmv_growth": "+140%"},
                        "media_urls": ["https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=600"],
                    }
                ],
            },
            {
                "name": "UrbanPulse Creative",
                "slug": "urbanpulse-creative",
                "tagline": "Next-gen video reels & influencer activations for fashion and beauty.",
                "description": "UrbanPulse transforms fashion and cosmetics brands with viral short-form video content, micro-influencer seeding, and brand visual design.",
                "city": "Mumbai",
                "state": "Maharashtra",
                "remote_or_local": "both",
                "team_size": "1-10",
                "founded_year": 2022,
                "category_specialties": ["Fashion & Apparel", "Beauty & Personal Care", "Jewellery & Accessories"],
                "service_offerings": ["Product videography", "Instagram management", "Influencer marketing", "Branding"],
                "min_budget_inr": 15000,
                "max_budget_inr": 80000,
                "gst_number": "27AABCU5678M1Z2",
                "verification_status": "verified",
                "is_featured": False,
                "is_demo": True,
                "rating_avg": 4.8,
                "reviews_count": 5,
                "email": "contact@urbanpulse.demo.in",
                "website": "https://urbanpulse.demo.in",
                "services": [
                    {
                        "name": "Short-Form Video Production",
                        "category": "Product videography",
                        "description": "Engaging model and unboxing reels tailored for Instagram and YouTube Shorts.",
                        "deliverables": ["8 edited reels", "Trending audio selection", "Hook scriptwriting"],
                        "min_price_inr": 15000,
                        "pricing_model": "monthly_retainer",
                    }
                ],
                "packages": [
                    {
                        "name": "Reels & Social Momentum",
                        "package_tier": "growth",
                        "price_inr": 18000,
                        "billing_interval": "monthly",
                        "description": "Monthly short-form video package focused on brand reach and community engagement.",
                        "deliverables": ["10 video reels", "Caption copywriting", "Hashtag strategy"],
                        "turnaround_days": 20,
                    }
                ],
                "portfolios": [
                    {
                        "client_brand_name": "Sahyadri Weaves",
                        "category": "Fashion & Apparel",
                        "project_title": "Handloom Sari Reel Showcase",
                        "description": "Created 6 artisanal storytelling reels highlighting traditional weavers, driving 250k organic views.",
                        "key_metrics": {"organic_views": "250K", "saves": "1,400+", "follower_growth": "+3,200"},
                        "media_urls": ["https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600"],
                    }
                ],
            },
            {
                "name": "ScaleMatrix Performance Labs",
                "slug": "scalematrix-labs",
                "tagline": "Technical e-commerce development and data-driven ad attribution.",
                "description": "ScaleMatrix combines high-speed Shopify Liquid engineering with rigorous multi-channel Google Search and Meta catalogue ads for scaling direct-to-consumer businesses.",
                "city": "Bengaluru",
                "state": "Karnataka",
                "remote_or_local": "remote",
                "team_size": "51-200",
                "founded_year": 2020,
                "category_specialties": ["Electronics", "Health & Wellness", "Consumer Goods", "Home & Living"],
                "service_offerings": ["Meta Ads management", "Google Ads management", "Shopify store development", "SEO"],
                "min_budget_inr": 25000,
                "max_budget_inr": 150000,
                "gst_number": "29AAECS9012K1Z5",
                "verification_status": "verification_pending",
                "is_featured": False,
                "is_demo": True,
                "rating_avg": 4.7,
                "reviews_count": 3,
                "email": "inbound@scalematrix.demo.in",
                "website": "https://scalematrix.demo.in",
                "services": [
                    {
                        "name": "Google Shopping & Search Mastery",
                        "category": "Google Ads management",
                        "description": "High-intent Performance Max and search keywords structured for maximum profit margins.",
                        "deliverables": ["PMax campaign structure", "Negative keyword harvesting", "ROAS target setting"],
                        "min_price_inr": 20000,
                        "pricing_model": "monthly_retainer",
                    }
                ],
                "packages": [
                    {
                        "name": "Omnichannel Ad Engine",
                        "package_tier": "premium",
                        "price_inr": 35000,
                        "billing_interval": "monthly",
                        "description": "Unified Meta Ads and Google Ads management with weekly attribution reporting.",
                        "deliverables": ["Meta + Google setup", "Dynamic catalogue retargeting", "Custom looker dashboard"],
                        "turnaround_days": 30,
                    }
                ],
                "portfolios": [
                    {
                        "client_brand_name": "Khurja Pottery Co.",
                        "category": "Home & Living",
                        "project_title": "Performance Max Direct-to-Consumer Transition",
                        "description": "Transitioned wholesale pottery brand to retail D2C store, driving 4.1x Google ROAS.",
                        "key_metrics": {"roas": "4.1x", "monthly_orders": "650+", "cpa_drop": "-28%"},
                        "media_urls": ["https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=600"],
                    }
                ],
            },
            {
                "name": "BrandCraft Studio",
                "slug": "brandcraft-studio",
                "tagline": "Distinctive brand identity, unboxing architecture, and packaging design.",
                "description": "BrandCraft Studio creates heritage, sustainable packaging, custom typography, and complete visual identities for premium Indian makers and D2C brands.",
                "city": "Jaipur",
                "state": "Rajasthan",
                "remote_or_local": "both",
                "team_size": "11-50",
                "founded_year": 2019,
                "category_specialties": ["Handicrafts & Decor", "Beauty & Personal Care", "Gifts & Festive", "Food & Beverage"],
                "service_offerings": ["Branding", "Packaging design", "Graphic design", "Marketing strategy and consultation"],
                "min_budget_inr": 18000,
                "max_budget_inr": 90000,
                "gst_number": "08AABCB4321P1Z9",
                "verification_status": "verified",
                "is_featured": True,
                "is_demo": True,
                "rating_avg": 4.9,
                "reviews_count": 12,
                "email": "hello@brandcraft.demo.in",
                "website": "https://brandcraft.demo.in",
                "services": [
                    {
                        "name": "Complete D2C Packaging & Unboxing Suite",
                        "category": "Packaging design",
                        "description": "Eco-friendly, drop-test compliant box, pouch, and label die-lines ready for offset printing.",
                        "deliverables": ["Master die-line vector files", "Print-ready CMYK PDFs", "3D photorealistic mockups"],
                        "min_price_inr": 18000,
                        "pricing_model": "project_based",
                    }
                ],
                "packages": [
                    {
                        "name": "Artisan Brand Identity Pack",
                        "package_tier": "starter",
                        "price_inr": 25000,
                        "billing_interval": "one_time",
                        "description": "Logo marks, color system, typography palette, and label templates for 3 SKUs.",
                        "deliverables": ["Brand Guidelines Book", "Vector Logo Assets", "3 SKU packaging templates"],
                        "turnaround_days": 21,
                    }
                ],
                "portfolios": [
                    {
                        "client_brand_name": "Royal Thar Terracotta",
                        "category": "Home & Living",
                        "project_title": "Heritage Clay Cookware Rebrand",
                        "description": "Redesigned terracotta cookware packaging with corrugated protection, reducing transit breakage by 94%.",
                        "key_metrics": {"damage_rate": "<0.6%", "perceived_value": "+45%", "repeat_orders": "+32%"},
                        "media_urls": ["https://images.unsplash.com/photo-1590490360182-c33d57733427?w=600"],
                    }
                ],
            },
            {
                "name": "GrowthOrbit Digital",
                "slug": "growthorbit-digital",
                "tagline": "Scalable customer acquisition, creative sprint testing, and high-ROAS Meta Ads.",
                "description": "GrowthOrbit is a data-obsessed growth partner for D2C brands. We manage over ₹15L in monthly ad spend across Meta and Google with proprietary creative fatigue algorithms.",
                "city": "Gurgaon",
                "state": "Haryana",
                "remote_or_local": "remote",
                "team_size": "11-50",
                "founded_year": 2021,
                "category_specialties": ["Food & Beverage", "Health & Wellness", "Beauty & Personal Care", "Home & Living"],
                "service_offerings": ["Meta Ads management", "Google Ads management", "Digital marketing", "Social media management"],
                "min_budget_inr": 20000,
                "max_budget_inr": 120000,
                "gst_number": "06AABCG7890Q1Z3",
                "verification_status": "verified",
                "is_featured": True,
                "is_demo": True,
                "rating_avg": 4.8,
                "reviews_count": 9,
                "email": "growth@growthorbit.demo.in",
                "website": "https://growthorbit.demo.in",
                "services": [
                    {
                        "name": "D2C Meta Ads Scale Sprint",
                        "category": "Meta Ads management",
                        "description": "Audience segmentation, creative testing sprints, and Advantage+ shopping campaigns.",
                        "deliverables": ["Weekly ad variant refreshes", "Custom audience LALs", "Daily budget pacing"],
                        "min_price_inr": 20000,
                        "pricing_model": "monthly_retainer",
                    }
                ],
                "packages": [
                    {
                        "name": "Growth Engine Retainer",
                        "package_tier": "growth",
                        "price_inr": 30000,
                        "billing_interval": "monthly",
                        "description": "Comprehensive Meta Ads management with weekly video and static creative iterations.",
                        "deliverables": ["Meta Ads manager", "12 ad iterations", "Bi-weekly strategy call"],
                        "turnaround_days": 30,
                    }
                ],
                "portfolios": [
                    {
                        "client_brand_name": "Satvik Superfoods",
                        "category": "Food & Beverage",
                        "project_title": "Organic Honey Festive Scale-Up",
                        "description": "Scaled organic honey brand from ₹3L to ₹18L monthly revenue with 4.4x blended ROAS.",
                        "key_metrics": {"blended_roas": "4.4x", "cac": "₹165", "monthly_gmv": "₹18 Lakh"},
                        "media_urls": ["https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=600"],
                    }
                ],
            },
            {
                "name": "MarketMinds Commerce",
                "slug": "marketminds-commerce",
                "tagline": "End-to-end marketplace management for Amazon.in, Flipkart, and Quick Commerce.",
                "description": "MarketMinds manages merchant operations, SP-API brand store optimization, A+ enhanced content, and Dark Store inventory forecasting for leading Indian marketplace sellers.",
                "city": "New Delhi",
                "state": "Delhi",
                "remote_or_local": "both",
                "team_size": "51-200",
                "founded_year": 2018,
                "category_specialties": ["Kitchen & Dining", "Electronics", "Baby & Kids", "Pet Supplies"],
                "service_offerings": ["Digital marketing", "Content creation", "SEO", "Marketing strategy and consultation"],
                "min_budget_inr": 22000,
                "max_budget_inr": 100000,
                "gst_number": "07AABCM6543R1Z7",
                "verification_status": "verified",
                "is_featured": False,
                "is_demo": True,
                "rating_avg": 4.9,
                "reviews_count": 14,
                "email": "partner@marketminds.demo.in",
                "website": "https://marketminds.demo.in",
                "services": [
                    {
                        "name": "Amazon India A+ Content & SP-API Setup",
                        "category": "Content creation",
                        "description": "Complete Brand Registry onboarding, A+ modules, Sponsored Products optimization, and Buy Box monitoring.",
                        "deliverables": ["A+ Enhanced Content", "Listing SEO keyword matrix", "Weekly advertising audit"],
                        "min_price_inr": 18000,
                        "pricing_model": "monthly_retainer",
                    }
                ],
                "packages": [
                    {
                        "name": "Marketplace Acceleration Pack",
                        "package_tier": "growth",
                        "price_inr": 28000,
                        "billing_interval": "monthly",
                        "description": "Dual Amazon and Flipkart listing optimization, stock reconciliation, and campaign management.",
                        "deliverables": ["Amazon SP-API", "Flipkart Seller Hub", "Bi-weekly inventory sync audit"],
                        "turnaround_days": 30,
                    }
                ],
                "portfolios": [
                    {
                        "client_brand_name": "Neer Water Pitchers",
                        "category": "Kitchen & Dining",
                        "project_title": "Amazon Prime Day Bestseller Rank #1",
                        "description": "Optimized copper pitcher listings with A+ content and negative keywords, driving 1,200 units during Prime Day.",
                        "key_metrics": {"category_rank": "#1 Bestseller", "prime_day_units": "1,200", "reviews": "+420"},
                        "media_urls": ["https://images.unsplash.com/photo-1544816155-12df9643f363?w=600"],
                    }
                ],
            },
            {
                "name": "SearchSpring Studio",
                "slug": "searchspring-studio",
                "tagline": "Organic Google ranking, high-converting product pages, and D2C SEO.",
                "description": "SearchSpring builds long-term organic traffic engines for Indian e-commerce brands through technical site audits, commercial intent keyword architectures, and schema markup.",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "remote_or_local": "remote",
                "team_size": "11-50",
                "founded_year": 2020,
                "category_specialties": ["Health & Wellness", "Fashion & Apparel", "Books & Stationery", "Artisan Goods"],
                "service_offerings": ["SEO", "Content creation", "E-commerce website development", "Marketing strategy and consultation"],
                "min_budget_inr": 15000,
                "max_budget_inr": 70000,
                "gst_number": "33AABCS8765T1Z1",
                "verification_status": "verified",
                "is_featured": False,
                "is_demo": True,
                "rating_avg": 4.8,
                "reviews_count": 7,
                "email": "rank@searchspring.demo.in",
                "website": "https://searchspring.demo.in",
                "services": [
                    {
                        "name": "E-Commerce Technical & Category SEO",
                        "category": "SEO",
                        "description": "Product schema indexing, collection page intent optimization, and core web vitals fixes.",
                        "deliverables": ["Technical crawl report", "15 optimized collection pages", "Monthly organic revenue tracking"],
                        "min_price_inr": 15000,
                        "pricing_model": "monthly_retainer",
                    }
                ],
                "packages": [
                    {
                        "name": "Organic Traffic Foundation",
                        "package_tier": "starter",
                        "price_inr": 18000,
                        "billing_interval": "monthly",
                        "description": "Keyword research, meta tag rewrites, and 4 high-authority commercial buying guide blogs per month.",
                        "deliverables": ["4 SEO articles", "Keyword tracking dashboard", "Site health monitoring"],
                        "turnaround_days": 30,
                    }
                ],
                "portfolios": [
                    {
                        "client_brand_name": "Dravida Silk Cottons",
                        "category": "Fashion & Apparel",
                        "project_title": "Organic Search Revenue Tripling",
                        "description": "Ranked #1 for 'pure mangalgiri cotton dress material' generating 18,000 monthly organic visitors.",
                        "key_metrics": {"organic_traffic": "+220%", "google_top_3_keywords": "48", "zero_ad_orders": "340/mo"},
                        "media_urls": ["https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600"],
                    }
                ],
            },
            {
                "name": "ScaleBridge Consulting",
                "slug": "scalebridge-consulting",
                "tagline": "Unit economics advisory, retention lifecycle, and WhatsApp marketing for makers.",
                "description": "ScaleBridge helps growing product makers understand contribution margins, optimize packaging logistics, and implement high-retention WhatsApp automated cart recovery.",
                "city": "Pune",
                "state": "Maharashtra",
                "remote_or_local": "both",
                "team_size": "1-10",
                "founded_year": 2021,
                "category_specialties": ["Home & Decor", "Beauty & Personal Care", "Organic & Sustainable", "Gourmet & Confectionery"],
                "service_offerings": ["Marketing strategy and consultation", "Email marketing", "Social media management", "Branding"],
                "min_budget_inr": 14000,
                "max_budget_inr": 65000,
                "gst_number": "27AABCS1982X1Z4",
                "verification_status": "verified",
                "is_featured": False,
                "is_demo": True,
                "rating_avg": 4.9,
                "reviews_count": 6,
                "email": "advisor@scalebridge.demo.in",
                "website": "https://scalebridge.demo.in",
                "services": [
                    {
                        "name": "WhatsApp Automation & Retention Setup",
                        "category": "Email marketing",
                        "description": "Abandoned cart recovery, order tracking updates, and repurchase automated flows via official WhatsApp Business API.",
                        "deliverables": ["4 automated WhatsApp flows", "Template approval", "Broadcast segment setup"],
                        "min_price_inr": 14000,
                        "pricing_model": "project_based",
                    }
                ],
                "packages": [
                    {
                        "name": "D2C Unit Economics & Retention Sprint",
                        "package_tier": "growth",
                        "price_inr": 22000,
                        "billing_interval": "monthly",
                        "description": "Margin analysis, courier volumetric weight audit, and repeat purchase lifecycle marketing.",
                        "deliverables": ["Margin audit sheet", "WhatsApp + Email retention flows", "Monthly unit economic review"],
                        "turnaround_days": 21,
                    }
                ],
                "portfolios": [
                    {
                        "client_brand_name": "Prakriti Organics",
                        "category": "Organic & Sustainable",
                        "project_title": "WhatsApp Cart Recovery 22% Conversion",
                        "description": "Deployed interactive WhatsApp cart abandonment sequences recovering ₹2.4L in lost checkout value monthly.",
                        "key_metrics": {"recovery_rate": "22.4%", "recovered_revenue": "₹2.4 Lakh/mo", "repeat_rate": "+38%"},
                        "media_urls": ["https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=600"],
                    }
                ],
            },
        ]

        seeded_count = 0
        for data in demo_agencies_data:
            slug = data.get("slug")
            existing = await db.scalar(select(AgencyProfile.id).where(AgencyProfile.slug == slug))
            if existing:
                continue

            services_data = data.pop("services", [])
            packages_data = data.pop("packages", [])
            portfolios_data = data.pop("portfolios", [])

            agency = AgencyProfile(
                organization_id=default_org_id,
                **data,
            )
            db.add(agency)
            await db.flush()

            for s_item in services_data:
                db.add(AgencyService(agency_profile_id=agency.id, target_industries=[], **s_item))

            for p_item in packages_data:
                db.add(AgencyServicePackage(agency_profile_id=agency.id, **p_item))

            for pf_item in portfolios_data:
                db.add(AgencyPortfolio(agency_profile_id=agency.id, **pf_item))

            seeded_count += 1

        if seeded_count > 0:
            await db.commit()
            logger.info(f"Successfully seeded {seeded_count} realistic demo agencies for Agency Connect marketplace.")
        else:
            logger.debug("Demo agencies already seeded.")

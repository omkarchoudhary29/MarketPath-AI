import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.agency import (
    AgencyPortfolio,
    AgencyProfile,
    AgencyService,
    AgencyServicePackage,
    SellerAgencyRequirement,
)
from backend.app.schemas.agency import (
    AgencyMatchCard,
    AgencyMatchExplanation,
    AgencyPackageRead,
    AgencyProfileRead,
    AgencyRecommendationResponse,
)

logger = logging.getLogger(__name__)

# Default hypothesis weights specified in prompt pack
DEFAULT_MATCHING_WEIGHTS = {
    "service_expertise_category_fit": 0.30,
    "required_service_coverage": 0.25,
    "budget_compatibility": 0.20,
    "portfolio_experience": 0.15,
    "location_and_availability": 0.10,
}


class AgencyMatchingEngine:
    """Hybrid recommendation engine combining deterministic eligibility filters with explainable weighted scoring."""

    @classmethod
    async def match_agencies_for_requirement(
        cls,
        db: AsyncSession,
        requirement: SellerAgencyRequirement,
        weights: Optional[Dict[str, float]] = None,
        include_demo: bool = True,
        min_match_threshold: int = 25,
    ) -> AgencyRecommendationResponse:
        """Executes two-phase matching: Hard Eligibility Filtering followed by Transparent Weighted Scoring."""
        active_weights = weights or DEFAULT_MATCHING_WEIGHTS

        # 1. Fetch active agencies with eager loading of services, packages, and portfolios
        stmt = (
            select(AgencyProfile)
            .options(
                selectinload(AgencyProfile.services),
                selectinload(AgencyProfile.packages),
                selectinload(AgencyProfile.portfolios),
            )
            .where(AgencyProfile.is_active.is_(True))
        )
        if not include_demo:
            stmt = stmt.where(AgencyProfile.is_demo.is_(False))

        res = await db.execute(stmt)
        agencies = res.scalars().all()

        eligible_cards: List[AgencyMatchCard] = []

        for agency in agencies:
            # Phase 1: Hard Eligibility Verification
            is_eligible, ineligibility_reason = cls._check_eligibility(agency, requirement)
            if not is_eligible:
                continue

            # Phase 2: Weighted Scoring
            score, breakdown, explanation = cls._calculate_match_score(
                agency, requirement, active_weights
            )

            if score >= min_match_threshold:
                agency_read = AgencyProfileRead.model_validate(agency)
                packages_read = [
                    AgencyPackageRead.model_validate(p)
                    for p in agency.packages
                    if p.is_active
                ]

                card = AgencyMatchCard(
                    agency=agency_read,
                    packages=packages_read,
                    match_score=score,
                    is_eligible=True,
                    explanation=explanation,
                    is_featured=agency.is_featured,
                    is_saved=False,
                )
                eligible_cards.append(card)

        # Sort: Organic match score descending. (Featured agencies are clearly badged, but ranking remains organic)
        eligible_cards.sort(key=lambda c: c.match_score, reverse=True)

        return AgencyRecommendationResponse(
            total_eligible=len(eligible_cards),
            matches=eligible_cards,
            weights_applied=active_weights,
            filtering_metadata={
                "seller_category": requirement.product_category,
                "requested_services_count": len(requirement.required_services),
                "seller_budget_inr": requirement.monthly_budget_inr or requirement.project_budget_inr,
                "preferred_location": requirement.preferred_location or requirement.location,
                "remote_or_local_preference": requirement.remote_or_local,
            },
        )

    @classmethod
    def _check_eligibility(
        cls, agency: AgencyProfile, req: SellerAgencyRequirement
    ) -> Tuple[bool, Optional[str]]:
        """Phase 1: Deterministic Hard Filters. Rejects incompatible candidates."""
        # Agency availability
        if not agency.is_available:
            return False, "Agency is currently marked as unavailable for new client engagements."

        # Verification status check: reject rejected or suspended
        if agency.verification_status in ["rejected", "suspended"]:
            return False, f"Agency standing is currently {agency.verification_status}."

        # Location & delivery mode compatibility
        if req.remote_or_local == "local":
            # If seller demands strictly local service, agency must either be in same city/state or explicitly offer local
            same_geo = (
                agency.city.lower() == req.location.lower()
                or (req.preferred_location and agency.city.lower() == req.preferred_location.lower())
                or agency.state.lower() == req.location.lower()
            )
            if not same_geo and agency.remote_or_local == "remote":
                return False, "Seller strictly requires local engagement, but agency operates purely remotely."

        # Budget hard threshold (agency minimum retainer cannot exceed seller monthly/project budget by > 25%)
        seller_budget = req.monthly_budget_inr or req.project_budget_inr or req.total_budget_inr
        if seller_budget and seller_budget > 0:
            if agency.min_budget_inr > (seller_budget * 1.25):
                return False, f"Agency minimum budget (₹{agency.min_budget_inr:,}) exceeds seller budget (₹{seller_budget:,}) by more than 25%."

        # Category or service overlap: must offer at least one requested capability or category specialty
        agency_services_lower = [s.name.lower() for s in agency.services] + [
            s.lower() for s in agency.service_offerings
        ]
        agency_categories_lower = [c.lower() for c in agency.category_specialties]

        req_services_lower = [s.lower() for s in req.required_services]
        req_cat_lower = req.product_category.lower()

        has_service_overlap = any(
            any(req_s in ag_s or ag_s in req_s for ag_s in agency_services_lower)
            for req_s in req_services_lower
        )
        has_cat_overlap = any(
            req_cat_lower in ag_c or ag_c in req_cat_lower for ag_c in agency_categories_lower
        )

        if not has_service_overlap and not has_cat_overlap and req_services_lower:
            return False, "Agency does not cover any of the requested marketing capabilities or category specialties."

        return True, None

    @classmethod
    def _calculate_match_score(
        cls,
        agency: AgencyProfile,
        req: SellerAgencyRequirement,
        weights: Dict[str, float],
    ) -> Tuple[int, Dict[str, float], AgencyMatchExplanation]:
        """Phase 2: Computes explainable weighted ranking score out of 100."""
        score_breakdown: Dict[str, float] = {}

        # 1. Service Expertise & Category Fit (30%)
        # Overlap with product category
        agency_cats = [c.lower() for c in agency.category_specialties]
        cat_match = 1.0 if any(req.product_category.lower() in c or c in req.product_category.lower() for c in agency_cats) else 0.4
        score_breakdown["category_fit"] = cat_match * 100

        # 2. Required Service Coverage (25%)
        agency_services_all = [s.name.lower() for s in agency.services] + [
            s.lower() for s in agency.service_offerings
        ]
        covered_services = []
        for req_s in req.required_services:
            if any(req_s.lower() in ag_s or ag_s in req_s.lower() for ag_s in agency_services_all):
                covered_services.append(req_s)

        coverage_ratio = (
            len(covered_services) / max(len(req.required_services), 1)
            if req.required_services
            else 0.8
        )
        score_breakdown["service_coverage"] = min(coverage_ratio, 1.0) * 100

        # 3. Budget Compatibility (20%)
        seller_budget = req.monthly_budget_inr or req.project_budget_inr or req.total_budget_inr or 25000
        if agency.min_budget_inr <= seller_budget:
            # Ideal: minimum budget is within seller budget
            budget_score = 1.0
            budget_note = f"Starting price (₹{agency.min_budget_inr:,}) is comfortably within your budget (₹{seller_budget:,})."
        elif agency.min_budget_inr <= seller_budget * 1.25:
            # Slightly higher but manageable
            budget_score = 0.7
            budget_note = f"Starting price (₹{agency.min_budget_inr:,}) is slightly above your budget (₹{seller_budget:,}) but negotiable on package scope."
        else:
            budget_score = 0.3
            budget_note = f"Agency starting price (₹{agency.min_budget_inr:,}) exceeds standard budget."
        score_breakdown["budget_compatibility"] = budget_score * 100

        # 4. Portfolio & Relevant Experience (15%)
        portfolio_highlights = []
        matching_portfolio_count = 0
        for p in agency.portfolios:
            is_relevant_cat = req.product_category.lower() in p.category.lower() or p.category.lower() in req.product_category.lower()
            if is_relevant_cat:
                matching_portfolio_count += 1
                portfolio_highlights.append(f"{p.client_brand_name} ({p.project_title}): {p.description[:80]}...")
            elif len(portfolio_highlights) < 2:
                portfolio_highlights.append(f"{p.client_brand_name}: {p.project_title}")

        portfolio_score = min(0.4 + (matching_portfolio_count * 0.3), 1.0) if agency.portfolios else 0.3
        score_breakdown["portfolio_experience"] = portfolio_score * 100

        # 5. Location and Availability (10%)
        loc_score = 0.5
        loc_note = "Offers Pan-India remote services."
        if agency.city.lower() == req.location.lower() or (req.preferred_location and agency.city.lower() == req.preferred_location.lower()):
            loc_score = 1.0
            loc_note = f"Local presence in {agency.city} matching your business location."
        elif agency.remote_or_local in ["remote", "both"]:
            loc_score = 0.8
            loc_note = f"Headquartered in {agency.city}, providing verified remote collaboration."
        score_breakdown["location_availability"] = loc_score * 100

        # Calculate final aggregated weighted score
        final_score = int(
            score_breakdown["category_fit"] * weights.get("service_expertise_category_fit", 0.30)
            + score_breakdown["service_coverage"] * weights.get("required_service_coverage", 0.25)
            + score_breakdown["budget_compatibility"] * weights.get("budget_compatibility", 0.20)
            + score_breakdown["portfolio_experience"] * weights.get("portfolio_experience", 0.15)
            + score_breakdown["location_availability"] * weights.get("location_and_availability", 0.10)
        )
        final_score = max(1, min(100, final_score))

        # Build transparent explanation
        why_parts = []
        if cat_match >= 0.8:
            why_parts.append(f"Specialized industry expertise in {req.product_category}")
        if covered_services:
            why_parts.append(f"Offers {len(covered_services)} of your {len(req.required_services)} requested services")
        if loc_score >= 0.8:
            why_parts.append(f"Strong geographic compatibility ({agency.city})")

        why_matched = "Matches because: " + "; ".join(why_parts) + "."

        missing_info = None
        if not agency.portfolios:
            missing_info = "Portfolio case studies currently pending agency upload."
        elif not agency.packages:
            missing_info = "Fixed packages pending; custom quote required."

        verification_standing = (
            "Verified Partner"
            if agency.verification_status == "verified"
            else "Registration Complete (Verification Pending)"
            if agency.verification_status == "verification_pending"
            else f"Registered ({agency.verification_status.title()})"
        )

        explanation = AgencyMatchExplanation(
            why_matched=why_matched,
            services_covered=covered_services or agency.service_offerings[:3],
            portfolio_highlights=portfolio_highlights[:2],
            budget_compatibility_note=budget_note,
            location_compatibility_note=loc_note,
            verification_standing=verification_standing,
            missing_or_uncertain_info=missing_info,
            score_breakdown=score_breakdown,
        )

        return final_score, score_breakdown, explanation

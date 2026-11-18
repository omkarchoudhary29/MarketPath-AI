import json
import logging
from typing import List, Optional
from google import genai
from google.genai import types

from backend.app.core.config import settings
from backend.app.schemas.agency import (
    AIRequirementExtractionRequest,
    AIRequirementExtractionResponse,
)

logger = logging.getLogger(__name__)

STANDARD_SERVICE_CATEGORIES = [
    "Digital marketing",
    "Social media management",
    "Meta Ads management",
    "Google Ads management",
    "SEO",
    "Shopify store development",
    "E-commerce website development",
    "Product photography",
    "Product videography",
    "Graphic design",
    "Branding",
    "Packaging design",
    "Influencer marketing",
    "Content creation",
    "Email marketing",
    "Marketing strategy and consultation",
]


class AgencyAIService:
    """Uses Gemini 2.5 Flash to transform raw seller inputs into structured agency search briefs."""

    @staticmethod
    def is_gemini_configured() -> bool:
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() != "")

    @classmethod
    async def extract_and_structure_requirements(
        cls, request: AIRequirementExtractionRequest
    ) -> AIRequirementExtractionResponse:
        """Transforms seller inputs into a structured brief with recommendations and missing info alerts."""
        if not cls.is_gemini_configured():
            return cls._fallback_extraction(request)

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            system_prompt = (
                "You are the MarketPath Agency Connect AI Assistant. Your role is to analyze a D2C seller's "
                "business profile, marketing objectives, and budget to formulate a structured agency search brief.\n"
                "CRITICAL RULES:\n"
                "1. Ground all summaries strictly in the provided seller details.\n"
                "2. Suggest relevant complementary services only from the 16 approved categories.\n"
                "3. Flag missing operational information that would prevent an agency from preparing an accurate quote.\n"
                "4. Provide honest budget guidance for the Indian D2C ecosystem (in INR).\n"
                "5. Never hallucinate or assume unstated business metrics.\n"
                "Output STRICTLY valid JSON conforming to the requested schema."
            )

            user_prompt = f"""
Analyze the following D2C brand requirements:
- Brand Name: {request.brand_name}
- Product Category: {request.product_category}
- Business Stage: {request.business_stage}
- City/Location: {request.location}
- Selected Objectives: {', '.join(request.selected_objectives) if request.selected_objectives else 'None specified'}
- Selected Services: {', '.join(request.selected_services) if request.selected_services else 'None specified'}
- Monthly Marketing Budget: ₹{request.monthly_budget_inr or 0:,} INR
- Project / One-time Budget: ₹{request.project_budget_inr or 0:,} INR
- Seller Notes / Brief: {request.raw_brief_text or 'None'}

Supported Agency Service Categories:
{', '.join(STANDARD_SERVICE_CATEGORIES)}

Generate a JSON object matching this schema:
{{
  "search_brief": "A professional 2-3 paragraph agency brief summarizing brand background, core challenges, and exact RFP scope.",
  "detected_category": "Standardized category name",
  "detected_stage": "Early Stage / Scaling / Mature",
  "identified_objectives": ["List of clarified business objectives"],
  "identified_services": ["List of confirmed requested services from approved list"],
  "suggested_additional_services": ["1-3 complementary services that would strengthen this specific campaign"],
  "missing_information_alerts": ["Important gaps an agency will need clarified (e.g. ad spend budget, existing catalogue size, target audience demographics)"],
  "budget_advisory": "Pragmatic assessment of whether this budget is sufficient for agency retainers vs one-time setup fees in India."
}}
"""
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[user_prompt],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )

            data = json.loads(response.text)
            return AIRequirementExtractionResponse(
                search_brief=data.get("search_brief", f"Agency brief for {request.brand_name}."),
                detected_category=data.get("detected_category", request.product_category),
                detected_stage=data.get("detected_stage", request.business_stage),
                identified_objectives=data.get("identified_objectives", request.selected_objectives),
                identified_services=data.get("identified_services", request.selected_services),
                suggested_additional_services=data.get("suggested_additional_services", []),
                missing_information_alerts=data.get("missing_information_alerts", []),
                budget_advisory=data.get("budget_advisory", "Budget suitable for standard agency retainers."),
                is_ai_generated=True,
            )

        except Exception as e:
            logger.warning(f"Gemini AI extraction failed or timed out: {e}. Falling back to deterministic rules.")
            return cls._fallback_extraction(request)

    @classmethod
    def _fallback_extraction(
        cls, request: AIRequirementExtractionRequest
    ) -> AIRequirementExtractionResponse:
        """Deterministic rule-based requirement extraction when offline or API is unconfigured."""
        brief_parts = [
            f"{request.brand_name} is an active D2C brand operating in the {request.product_category} sector based in {request.location}.",
            f"Currently in the '{request.business_stage}' stage, the brand seeks professional agency partnerships to drive measurable growth.",
        ]

        if request.selected_objectives:
            brief_parts.append(f"Primary business objectives include: {', '.join(request.selected_objectives)}.")

        if request.selected_services:
            brief_parts.append(f"Requested agency capabilities: {', '.join(request.selected_services)}.")

        if request.raw_brief_text:
            brief_parts.append(f"Specific seller directives: {request.raw_brief_text}")

        # Deterministic complementary services suggestions
        suggested = []
        if "Product photography" in request.selected_services and "Social media management" not in request.selected_services:
            suggested.append("Social media management")
        if "Meta Ads management" in request.selected_services and "Graphic design" not in request.selected_services:
            suggested.append("Graphic design")
        if "Shopify store development" in request.selected_services and "SEO" not in request.selected_services:
            suggested.append("SEO")
        if not suggested:
            suggested = ["Marketing strategy and consultation"]

        # Missing information alerts
        alerts = []
        if not request.monthly_budget_inr and not request.project_budget_inr:
            alerts.append("No monthly retainer or project budget specified. Agencies require budget guidance to estimate scope.")
        if not request.selected_objectives:
            alerts.append("No specific business objectives selected (e.g. ROAS target, CAC reduction, online sales volume).")
        if not request.raw_brief_text or len(request.raw_brief_text.strip()) < 20:
            alerts.append("Brief lacks details on current monthly revenue, ad spend budget, or previous agency experience.")

        budget_val = request.monthly_budget_inr or request.project_budget_inr or 0
        if budget_val < 10000:
            advisory = "Budget is below typical agency retainer thresholds (₹10,000/mo). Consider fixed one-time project packages or boutique freelancers."
        elif budget_val <= 30000:
            advisory = "Budget is well-suited for specialized boutique agencies and dedicated D2C growth consultants."
        else:
            advisory = "Budget is sufficient for full-funnel digital marketing agencies offering dedicated account management."

        return AIRequirementExtractionResponse(
            search_brief=" ".join(brief_parts),
            detected_category=request.product_category,
            detected_stage=request.business_stage,
            identified_objectives=request.selected_objectives,
            identified_services=request.selected_services,
            suggested_additional_services=suggested,
            missing_information_alerts=alerts,
            budget_advisory=advisory,
            is_ai_generated=False,
        )


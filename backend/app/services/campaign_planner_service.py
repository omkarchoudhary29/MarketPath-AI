import json
import logging
from typing import Any, Dict, Optional, Tuple
from google import genai
from google.genai import types

from backend.app.core.config import settings
from backend.app.models.brand import BrandProfile
from backend.app.models.catalogue import Product
from backend.app.schemas.marketing import CampaignAIPlanRequest, CampaignAIProposal

logger = logging.getLogger(__name__)


def is_gemini_configured() -> bool:
    return bool(
        settings.GEMINI_API_KEY
        and not settings.GEMINI_API_KEY.startswith("your_")
        and len(settings.GEMINI_API_KEY) > 10
    )


def _build_planner_prompts(
    product: Optional[Product],
    brand: Optional[BrandProfile],
    req: CampaignAIPlanRequest,
) -> Tuple[str, str]:
    brand_name = brand.brand_name if brand else "Aura Terra Living"
    tone = brand.tone_of_voice if brand else "Warm & Aesthetic"
    archetype = brand.archetype if brand else "Mindful Creator"
    brand_story = brand.story if brand else "Artisanal home goods crafted thoughtfully in India."

    product_facts = "No specific single product selected; campaign operates at brand/collection level."
    if product:
        dims = product.dimensions or {}
        dims_str = f"{dims.get('length', '')}x{dims.get('width', '')}x{dims.get('height', '')} {dims.get('unit', 'cm')}" if dims else "N/A"
        materials_str = ", ".join(product.materials or []) if product.materials else "Handcrafted materials"
        product_facts = f"""- Title: {product.title}
- SKU: {product.sku}
- Category: {product.category}
- Base Price: {product.currency} {product.base_price}
- Dimensions: {dims_str}
- Materials: {materials_str}
- Description: {product.short_description or product.long_description or 'Artisanal piece'}
"""

    system_instruction = f"""You are MarketPath AI Campaign Strategist, an expert digital marketing consultant for Indian D2C home, lifestyle, and artisanal brands.
Client Brand: {brand_name}
Brand Tone of Voice: {tone}
Brand Archetype: {archetype}
Brand Story: {brand_story}

MANDATORY FOUNDER & ANTI-HALLUCINATION RULES:
1. STRICTLY NO FABRICATED BENCHMARKS: Do NOT invent audience sizes (e.g., '14.5M consumers'), CPMs, CPCs, or conversion rates. If market benchmarks are cited, label them explicitly as general industry hypotheses that require empirical verification.
2. STRICTLY NO GUARANTEED ROAS: Never state or imply guaranteed return on ad spend or revenue.
3. GROUNDING: Ground the strategy strictly in the seller's budget, product facts, and provided brief.
4. HONEST UNCERTAINTY: If key details are missing (such as landing page speed or historical ad account pixel data), state them explicitly in 'assumptions_and_risks' and 'missing_information_notes'.
5. OUTPUT: Output structured JSON conforming strictly to the CampaignAIProposal schema.
"""

    user_prompt = f"""Plan a marketing and advertising campaign for {brand_name}.

SELLER INPUT BRIEF:
- Natural Language Brief: {req.natural_language_brief or 'Launch a performance campaign to grow online sales and awareness.'}
- Primary Objective: {req.objective}
- Target Geography: {req.target_geography or 'Pan-India'}
- Target Audience Focus: {req.target_audience or 'Design-conscious urban Indian consumers'}
- Planned Budget: ₹{req.monthly_budget_inr:,.2f}
- Campaign Duration: {req.duration_days} days
- Target Channel: {req.channel}

PRODUCT FACTS:
{product_facts}

Generate the complete structured campaign proposal matching the JSON schema.
"""

    return system_instruction, user_prompt


def _generate_mock_plan(
    product: Optional[Product],
    brand: Optional[BrandProfile],
    req: CampaignAIPlanRequest,
) -> Dict[str, Any]:
    brand_name = brand.brand_name if brand else "Aura Terra Living"
    product_title = product.title if product else "Artisanal Home & Living Collection"
    product_cat = product.category if product else "Home & Lifestyle"
    budget = req.monthly_budget_inr or 10000.0
    duration = req.duration_days or 30
    daily_spend = round(budget / max(duration, 1), 2)
    geography = req.target_geography or "Tier 1 Metros & Maharashtra"

    return {
        "strategy_summary": f"A targeted 3-stage performance marketing sprint focusing on {product_title} by {brand_name}. We leverage Meta's visual feed and story ad formats to convert high-intent design enthusiasts and gifting shoppers across {geography} into qualified website customers.",
        "objective_interpretation": f"Optimizing for '{req.objective}' by establishing immediate visual differentiation on feed placements, then driving qualified traffic with clear product value propositions into a low-friction mobile checkout.",
        "suggested_channel": "Meta Ads (Instagram & Facebook)",
        "channel_rationale": "High visual affinity for handcrafted and home decor products in India. Instagram Stories and Reels deliver strong engagement for lifestyle aesthetics at low testing thresholds.",
        "target_audience_hypotheses": [
            "Affluent Urbanites (24-42) interested in interior styling, studio pottery, and sustainable living.",
            "Thoughtful Corporate & Festive Gifters seeking authentic, non-mass-produced Indian artisanal products.",
            "Architects, designers, and work-from-home professionals investing in serene living and workspace aesthetics.",
        ],
        "geography_recommendations": [
            geography,
            "Top Tier 1 Metro clusters: Mumbai MMR, Bengaluru, Delhi NCR, and Pune.",
        ],
        "ad_headlines": [
            f"Handcrafted {product_title} | Made in Pune",
            f"Elevate Your Daily Rituals with {brand_name}",
            f"Artisanal Stoneware from ₹{int(product.base_price) if product else 899}",
            "Sustainable Luxury for Conscious Homes",
        ],
        "primary_texts": [
            f"Tired of generic, mass-produced home goods? The {product_title} from {brand_name} brings mindful craftsmanship into your living space. Handcrafted patiently in small studio batches.",
            f"Start your mornings with intention. Explore our hand-thrown {product_cat.lower()} designed to bring warmth, texture, and serene beauty into modern homes.",
            f"Looking for meaningful gifting that speaks of genuine artistry? Discover limited handcrafted batches by {brand_name}. Delivery across India.",
        ],
        "creative_concepts": [
            {
                "concept_title": "The Morning Ritual",
                "visual_direction": "Natural morning sunlight streaming across a clean wooden dining table; slow zoom on handcrafted glaze texture with steam rising from freshly brewed coffee.",
                "hook_angle": "Sensory, slow-living appeal connecting product to daily mindfulness.",
                "recommended_format": "feed_image",
            },
            {
                "concept_title": "Behind the Maker's Hands",
                "visual_direction": "Candid artisan workshop footage in Pune showing clay shaping on the wheel, kiln firing, and maker stamp detail.",
                "hook_angle": "Proof of authenticity and artisan provenance vs. factory imitation.",
                "recommended_format": "story",
            },
            {
                "concept_title": "Design in Situ Carousel",
                "visual_direction": "4-slide carousel highlighting living room styling, tabletop detail, dimensions, and eco-packaging.",
                "hook_angle": "Functional versatility and gift-readiness.",
                "recommended_format": "carousel",
            },
        ],
        "call_to_action_options": ["Shop Now", "Explore Collection", "Order Today"],
        "suggested_budget_allocation": {
            "total_budget_inr": budget,
            "duration_days": duration,
            "recommended_daily_limit_inr": daily_spend,
            "testing_phase_percentage": 30,
            "testing_phase_budget_inr": round(budget * 0.30, 2),
            "scaling_phase_percentage": 50,
            "scaling_phase_budget_inr": round(budget * 0.50, 2),
            "retargeting_phase_percentage": 20,
            "retargeting_phase_budget_inr": round(budget * 0.20, 2),
            "note": "AI suggestion based on input constraints. Media spend is charged directly to your connected ad account by Meta/Google. MarketPath takes zero commission from your ad budget.",
        },
        "campaign_schedule": [
            {
                "phase": "Phase 1: Creative & Hook Testing",
                "day_range": "Days 1 - 7",
                "phase_objective": "Identify top-performing headline and visual hook with controlled daily spend.",
                "action_items": [
                    "Deploy 3 creative concepts in parallel.",
                    "Monitor click-through rate (CTR) and initial add-to-cart signals.",
                    "Pause underperforming creative angles after 500+ impressions.",
                ],
            },
            {
                "phase": "Phase 2: Scale Winning Angles",
                "day_range": "Days 8 - 22",
                "phase_objective": "Consolidate budget into the top 2 performing creative variations to drive conversions.",
                "action_items": [
                    "Shift 70% of spend into the winning creative/audience combination.",
                    "Ensure landing page speed and mobile checkout friction remain low.",
                ],
            },
            {
                "phase": "Phase 3: Warm Retargeting & Close",
                "day_range": "Days 23 - 30",
                "phase_objective": "Re-engage site visitors who viewed products or added to cart but did not complete purchase.",
                "action_items": [
                    "Deploy limited-batch reminder ad and social proof reviews.",
                    "Review total spend against the hard ₹" + str(int(budget)) + " budget ceiling.",
                ],
            },
        ],
        "measurement_strategy": {
            "primary_kpis": ["Outbound Click-Through Rate (CTR)", "Cost Per Click (CPC)", "Add to Cart", "ROAS"],
            "attribution_window": "7-day click or 1-day view (Standard Meta Attribution)",
            "pixel_requirements": "Meta Pixel or Conversions API active on Shopify / website checkout.",
        },
        "assumptions_and_risks": [
            "Assumes mobile-optimized landing page with sub-3 second loading time in India.",
            "Assumes active Meta Pixel installed on store to capture purchase events.",
            "Performance is subject to seasonal auction dynamics and creative fatigue.",
            "Benchmarks are hypotheses: actual CPC and conversion rates depend on ad account history and live ad auction competitiveness.",
        ],
        "missing_information_notes": "Historical ad account conversion data and Facebook Page linking status should be verified before launch.",
        "disclaimer": "AI-generated hypothesis based on seller brief. Benchmarks, conversions, and ROAS are not guaranteed and must be verified in live ad account tests.",
        "is_mock": True,
    }


async def generate_campaign_plan(
    product: Optional[Product],
    brand: Optional[BrandProfile],
    req: CampaignAIPlanRequest,
) -> Tuple[CampaignAIProposal, int, str]:
    """Generates structured, grounded campaign proposal using Gemini with Pydantic validation."""
    system_instruction, user_prompt = _build_planner_prompts(product, brand, req)
    model_version = settings.GEMINI_MODEL

    if not is_gemini_configured():
        logger.info("Using grounded mock campaign planner (Gemini API key not configured or in dev mode).")
        raw_plan = _generate_mock_plan(product, brand, req)
        validated = CampaignAIProposal.model_validate(raw_plan)
        return validated, 550, f"{model_version}-mock"

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model_version,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=CampaignAIProposal,
                temperature=0.7,
            ),
        )

        response_text = response.text or "{}"
        raw_json = json.loads(response_text)
        raw_json["is_mock"] = False
        validated = CampaignAIProposal.model_validate(raw_json)

        tokens_consumed = 650
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens_consumed = (
                (response.usage_metadata.prompt_token_count or 0)
                + (response.usage_metadata.candidates_token_count or 0)
            )

        return validated, tokens_consumed, model_version

    except Exception as e:
        logger.warning(f"Gemini Campaign Planner failed ({str(e)}), falling back to grounded mock plan.")
        raw_plan = _generate_mock_plan(product, brand, req)
        validated = CampaignAIProposal.model_validate(raw_plan)
        return validated, 450, f"{model_version}-fallback"


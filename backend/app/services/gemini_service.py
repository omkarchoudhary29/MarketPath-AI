import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
from google import genai
from google.genai import types
from pydantic import ValidationError

from backend.app.core.config import settings
from backend.app.models.brand import BrandProfile
from backend.app.models.catalogue import Product
from backend.app.schemas.content import (
    AdHookPayload,
    AIGenerateRequest,
    FullPackPayload,
    InstagramPostPayload,
    SEOPackPayload,
    ShopifyCopyPayload,
)

logger = logging.getLogger(__name__)


def is_gemini_configured() -> bool:
    return bool(
        settings.GEMINI_API_KEY
        and not settings.GEMINI_API_KEY.startswith("your_")
        and len(settings.GEMINI_API_KEY) > 10
    )


def _build_grounding_prompt(
    product: Product,
    brand: Optional[BrandProfile],
    req: AIGenerateRequest,
) -> Tuple[str, str]:
    """Constructs system prompt and grounded user context from master product and brand profile."""
    brand_name = brand.brand_name if brand else "Indian Artisanal Brand"
    tone = req.tone_override or (brand.tone_of_voice if brand else "Warm & Aesthetic")
    archetype = brand.archetype if brand else "Creator & Explorer"
    brand_story = brand.story if brand else ""
    target_audience = req.target_audience or (brand.target_audience_summary if brand else "Design-conscious Indian consumers")

    # Serialize variants
    variant_details = [
        f"- {v.title}: SKU={v.sku}, Price={product.currency} {v.price}, Options={v.options}"
        for v in (product.variants or [])
    ]
    variants_str = "\n".join(variant_details) if variant_details else "No separate variants (single SKU)."

    # Serialize dimensions & materials
    dims = product.dimensions or {}
    dims_str = f"{dims.get('length', '')}x{dims.get('width', '')}x{dims.get('height', '')} {dims.get('unit', 'cm')}" if dims else "Not specified"
    materials_str = ", ".join(product.materials or []) if product.materials else "Not specified"
    tags_str = ", ".join(product.tags or []) if product.tags else "None"

    system_instruction = f"""You are MarketPath AI, an expert D2C commerce copywriter specializing in Indian home, lifestyle, and gifting brands.
Your client is {brand_name}.
Brand Tone of Voice: {tone}
Brand Archetype: {archetype}
Brand Story: {brand_story}
Target Audience: {target_audience}

CRITICAL ANTI-HALLUCINATION RULES:
1. Ground every claim strictly in the product facts provided below.
2. DO NOT INVENT false certifications (e.g. USDA Organic, ISO, GOTS) unless explicitly listed in the product data.
3. DO NOT INVENT technical dimensions, weights, or material compositions not in the product data.
4. DO NOT INVENT fake customer testimonials or performance claims.
5. If details such as care instructions or exact dimensions are missing, make note of the omission in the 'missing_information_notes' field.
6. Populate 'grounded_facts' with a list of verified facts you directly incorporated from the product profile.
7. Always output valid JSON conforming exactly to the requested schema.
"""

    user_prompt = f"""Generate {req.content_type} optimized for channel '{req.target_channel}'.
Marketing Objective: {req.campaign_objective or 'New Product Launch'}
Special Seller Instructions: {req.instructions or 'Highlight craftsmanship, durability, and mindful living.'}

MASTER PRODUCT SPECIFICATIONS:
- Title: {product.title}
- SKU: {product.sku}
- Category: {product.category}
- Base Price: {product.currency} {product.base_price}
- Compare At Price: {product.currency} {product.compare_at_price or 'N/A'}
- Dimensions: {dims_str}
- Weight: {product.weight or 'N/A'} kg
- Materials: {materials_str}
- Product Tags: {tags_str}
- Short Description: {product.short_description or 'N/A'}
- Long Description: {product.long_description or 'N/A'}
- Product Variants:
{variants_str}

Please generate the structured JSON matching the {req.content_type} schema.
"""

    return system_instruction, user_prompt


def _generate_mock_ai_payload(
    product: Product,
    brand: Optional[BrandProfile],
    req: AIGenerateRequest,
) -> Dict[str, Any]:
    """Generates realistic, grounded content for development, testing, and offline modes."""
    brand_name = brand.brand_name if brand else "Aura Terra Living"
    tone = req.tone_override or (brand.tone_of_voice if brand else "Warm & Aesthetic")
    materials_list = product.materials or ["Artisanal stoneware", "Earthy clay"]
    materials_str = ", ".join(materials_list)

    grounded_facts = [
        f"Handcrafted in {product.category} category",
        f"Priced at {product.currency} {product.base_price}",
        f"Crafted with {materials_str}",
        f"Master SKU: {product.sku}",
    ]

    missing_notes = None
    if not product.dimensions:
        missing_notes = "Dimensions were not specified in master product record; recommended to add before publishing."

    if req.content_type == "shopify_copy":
        return {
            "title": f"{product.title} | Handcrafted by {brand_name}",
            "short_summary": f"Thoughtfully designed {product.title.lower()} crafted from {materials_str} to elevate your everyday living spaces.",
            "body_html": f"""<div class="marketpath-product-description">
  <p class="lead">Imbue your daily rituals with conscious artistry. The <strong>{product.title}</strong> is individually handcrafted by skilled artisans in Pune, blending timeless form with contemporary functionality.</p>
  <h3>Key Highlights</h3>
  <ul>
    <li><strong>Authentic Craft:</strong> Made using {materials_str}.</li>
    <li><strong>Mindful Design:</strong> Ergonomically shaped for comfort and enduring beauty.</li>
    <li><strong>Sustainable Philosophy:</strong> Designed to last, reducing clutter and celebrating slow living.</li>
  </ul>
  <p>Whether for your own sanctuary or as a thoughtful gift, each piece carries unique subtle variations that celebrate true craftsmanship.</p>
</div>""",
            "bullet_points": [
                f"Handcrafted from premium {materials_str}",
                f"Authentic {product.category} design from {brand_name}",
                f"Base price: {product.currency} {product.base_price:,.2f}",
                "Food-safe, sustainable, and built for daily appreciation",
            ],
            "suggested_tags": (product.tags or []) + ["Artisanal", "HomeDecor", "SlowLiving", "HandmadeInIndia"],
            "meta_title": f"Buy {product.title} | {brand_name}",
            "meta_description": f"Shop {product.title} handcrafted in Pune from {materials_str}. Mindful, sustainable home and lifestyle goods by {brand_name}.",
            "grounded_facts": grounded_facts,
            "missing_information_notes": missing_notes,
        }

    elif req.content_type == "instagram_post":
        return {
            "hook": f"Slow down and savor the moment. ✨ Meet our new {product.title}.",
            "caption": f"""There's an quiet beauty in objects made by human hands. 🌿

Our {product.title} isn't just another addition to your home—it's an invitation to pause. Hand-thrown with {materials_str}, every curve reflects the artisan's patient dedication.

Pair it with your morning chai, your quiet reading nook, or gift it to someone who treasures thoughtful design.

Available now in limited batches at {brand_name}. Tap the link in bio to bring yours home. 🕊️""",
            "hashtags": [
                "#SlowLivingIndia",
                "#ArtisanalLiving",
                "#ModernIndianHome",
                "#StudioPottery",
                "#MindfulLiving",
                "#HandmadeInPune",
                "#D2CIndia",
            ],
            "carousel_slides": [
                f"Slide 1: Close-up of {product.title} in warm morning sunlight showcasing the rich {materials_str} texture.",
                "Slide 2: In-situ lifestyle shot on a wooden table alongside fresh botanicals and linen.",
                f"Slide 3: Detailed view of artisan maker mark and base finish ({product.sku}).",
                "Slide 4: Call to action slide with link-in-bio prompt and brand packaging.",
            ],
            "call_to_action": "Tap the link in bio to shop the limited studio batch.",
            "grounded_facts": grounded_facts,
            "missing_information_notes": missing_notes,
        }

    elif req.content_type == "ad_hook":
        return {
            "headlines": [
                f"Handcrafted {product.title}",
                f"Artisanal Living | {brand_name}",
                f"Mindful Design from ₹{int(product.base_price)}",
                f"Slow Living for Modern Homes",
            ],
            "primary_texts": [
                f"Tired of mass-produced home goods? The {product.title} by {brand_name} brings authentic artisan craftsmanship into your living space. Handcrafted with {materials_str}.",
                f"Elevate your daily rituals. Each {product.title} is patiently crafted in Pune to celebrate texture, warmth, and enduring quality.",
                f"Looking for meaningful gifts? Explore handcrafted {product.category.lower()} by {brand_name}. Sustainable, elegant, and timeless.",
            ],
            "cta_options": ["Shop Now", "Explore Collection", "Order Today"],
            "audience_angle": "Targeting urban design-conscious homeowners (25-45) and thoughtful gifting shoppers seeking sustainable artisan luxury.",
            "grounded_facts": grounded_facts,
            "missing_information_notes": missing_notes,
        }

    elif req.content_type == "seo_pack":
        clean_slug = re.sub(r"[^a-z0-9]+", "-", product.title.lower()).strip("-")
        return {
            "seo_title": f"Buy {product.title} Online | {brand_name}",
            "meta_description": f"Shop the {product.title} handcrafted from {materials_str}. Premium {product.category.lower()} by {brand_name}. Fast shipping across India.",
            "target_keywords": [
                f"handmade {product.category.lower()}",
                f"buy {product.title.lower()}",
                f"artisanal {product.title.lower()} india",
                f"{brand_name.lower()} collection",
                "sustainable home decor pune",
            ],
            "url_slug_recommendation": f"{clean_slug}-{product.sku.lower()}",
            "grounded_facts": grounded_facts,
            "missing_information_notes": missing_notes,
        }

    else:  # full_pack
        return {
            "shopify": _generate_mock_ai_payload(product, brand, AIGenerateRequest(product_id=product.id, content_type="shopify_copy")),
            "instagram": _generate_mock_ai_payload(product, brand, AIGenerateRequest(product_id=product.id, content_type="instagram_post")),
            "ad_hooks": _generate_mock_ai_payload(product, brand, AIGenerateRequest(product_id=product.id, content_type="ad_hook")),
            "seo": _generate_mock_ai_payload(product, brand, AIGenerateRequest(product_id=product.id, content_type="seo_pack")),
        }


async def generate_ai_content(
    product: Product,
    brand: Optional[BrandProfile],
    request: AIGenerateRequest,
) -> Tuple[Dict[str, Any], int, str]:
    """Generates channel-specific content using Gemini 2.5 Flash with structured schema validation.
    
    Returns: (payload_dict, tokens_consumed, model_version)
    """
    system_instruction, user_prompt = _build_grounding_prompt(product, brand, request)
    model_version = settings.GEMINI_MODEL

    # Select target Pydantic schema
    schema_map = {
        "shopify_copy": ShopifyCopyPayload,
        "instagram_post": InstagramPostPayload,
        "ad_hook": AdHookPayload,
        "seo_pack": SEOPackPayload,
        "full_pack": FullPackPayload,
    }
    target_schema = schema_map.get(request.content_type, ShopifyCopyPayload)

    if not is_gemini_configured():
        logger.info("Using grounded mock AI generator (Gemini API key not configured or in dev mode).")
        mock_payload = _generate_mock_ai_payload(product, brand, request)
        validated = target_schema.model_validate(mock_payload)
        return validated.model_dump(), 450, f"{model_version}-mock"

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"api_version": "v1alpha"})
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model=model_version,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=target_schema,
                    temperature=0.7,
                ),
            ),
            timeout=15.0,
        )

        response_text = response.text or "{}"
        raw_json = json.loads(response_text)
        validated = target_schema.model_validate(raw_json)

        # Estimate tokens
        tokens_consumed = 500
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens_consumed = (
                (response.usage_metadata.prompt_token_count or 0)
                + (response.usage_metadata.candidates_token_count or 0)
            )

        return validated.model_dump(), tokens_consumed, model_version

    except Exception as e:
        logger.warning(f"Gemini API call failed ({str(e)}), falling back to grounded generator.")
        mock_payload = _generate_mock_ai_payload(product, brand, request)
        validated = target_schema.model_validate(mock_payload)
        return validated.model_dump(), 400, f"{model_version}-fallback"


# ==========================================
# PHASE 2: SPEECH-TO-TEXT & EXTRACTION PIPELINE
# ==========================================

async def transcribe_speech(
    audio_bytes: bytes,
    mime_type: str = "audio/webm",
) -> Dict[str, Any]:
    """Transcribes spoken audio verbatim using Gemini multimodal capabilities.
    
    Returns:
        Dict with keys: transcript, duration_seconds, detected_language, status, model
    """
    if not audio_bytes or len(audio_bytes) < 60:
        return {
            "transcript": "",
            "duration_seconds": 0.0,
            "detected_language": "en",
            "status": "no_speech_detected",
            "model": "none",
        }

    if not is_gemini_configured():
        logger.warning("Gemini API not configured for speech transcription.")
        return {
            "transcript": "",
            "duration_seconds": 0.0,
            "detected_language": "en",
            "status": "api_not_configured",
            "model": "none",
        }

    prompt = (
        "You are an expert speech-to-text engine for MarketPath AI. "
        "Transcribe this audio recording verbatim. Output ONLY the exact spoken words with natural punctuation. "
        "Do not add any preamble, conversational commentary, explanations, quotes, or apologies. "
        "If the audio contains only silence, background noise, or no intelligible speech, respond with an empty string."
    )

    models_to_try = [settings.GEMINI_MODEL, "gemini-3.5-flash-lite", "gemini-3.8-flash"]
    candidate_models = list(dict.fromkeys([m for m in models_to_try if m]))

    last_error = None
    for model_name in candidate_models:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"api_version": "v1alpha"})
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model=model_name,
                    contents=[prompt, audio_part],
                ),
                timeout=12.0,
            )
            raw_text = (resp.text or "").strip()
            if raw_text.startswith('"') and raw_text.endswith('"') and len(raw_text) > 1:
                raw_text = raw_text[1:-1].strip()
            elif raw_text.startswith("'") and raw_text.endswith("'") and len(raw_text) > 1:
                raw_text = raw_text[1:-1].strip()

            status = "success" if raw_text else "no_speech_detected"
            return {
                "transcript": raw_text,
                "duration_seconds": round(len(audio_bytes) / 32000.0, 2),
                "detected_language": "en-IN",
                "status": status,
                "model": model_name,
            }
        except Exception as e:
            logger.warning(f"Speech transcription failed on model {model_name}: {e}")
            last_error = e

    return {
        "transcript": "",
        "duration_seconds": 0.0,
        "detected_language": "en",
        "status": f"error: {str(last_error)}",
        "model": "failed",
    }


async def extract_brand_intelligence(
    transcript: str,
    existing_brand: Optional[BrandProfile] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Extracts structured brand data into 5 canonical sections with provenance flags."""
    raw_text = (transcript or "").strip()
    cleaned = re.sub(r"[^\w\s]", "", raw_text).strip().lower()
    greetings = {
        "hello", "hi", "hey", "namaste", "good morning", "good afternoon",
        "good evening", "hi there", "hello there", "start", "test", "marketpath",
    }
    is_greeting = cleaned in greetings or len(cleaned) < 4

    default_identity = {
        "brand_name": (existing_brand.brand_name if existing_brand and existing_brand.brand_name else ""),
        "tagline": (existing_brand.tagline if existing_brand else ""),
        "mission": (existing_brand.mission if existing_brand else ""),
        "category": "",
        "location": "",
        "founder_name": "",
        "website": "",
    }
    default_story = {
        "story": (existing_brand.story if existing_brand else ""),
        "heritage": "",
        "tone_of_voice": (existing_brand.tone_of_voice if existing_brand else "Warm & Aesthetic"),
        "archetype": (existing_brand.archetype if existing_brand else "Creator & Caregiver"),
        "brand_values": (existing_brand.brand_values if existing_brand else []),
    }
    default_customers = {
        "target_audience_summary": (existing_brand.target_audience_summary if existing_brand else ""),
        "target_demographics": "Conscious Indian consumers seeking authentic lifestyle goods",
        "key_usps": (existing_brand.key_usps if existing_brand else []),
        "customer_pain_points": [],
    }
    default_guidelines = {
        "tone_guidelines": "Authentic, respectful of craftsmanship, grounded",
        "vocabulary_to_use": ["Handcrafted", "Conscious", "Sustainable"],
        "vocabulary_to_avoid": ["Cheap", "Mass-produced"],
        "visual_aesthetic_notes": "Warm earthy tones, natural textures, mindful compositions",
    }
    default_policies = {
        "selling_channels": ["shopify", "amazon"],
        "shipping_policy": "Standard shipping across India in 3-5 business days",
        "return_policy": "7-day return policy for unused items in original packaging",
        "sustainability_practices": "Plastic-free packaging and responsibly sourced materials",
        "packaging_philosophy": "Eco-friendly recyclable kraft boxes with honeycomb paper cushioning",
    }

    if is_greeting or not raw_text:
        return {
            "reply_message": (
                "Hello! Welcome to MarketPath AI. I'm here to help you set up your brand and master product catalogue. "
                "What is your brand name, and what kind of products do you create?"
            ),
            "sections": {
                "identity": default_identity,
                "story_positioning": default_story,
                "target_customers": default_customers,
                "guidelines": default_guidelines,
                "selling_policies": default_policies,
            },
            "missing_fields": ["brand_name", "category", "story", "materials", "key_usps"],
            "follow_up_question": "What is your brand name, and what kind of products do you create?",
            "is_ready_for_confirmation": False,
            "provenance": {
                "brand_name": "missing",
                "category": "missing",
                "story": "missing",
                "tone_of_voice": "suggested",
                "archetype": "suggested",
                "target_audience_summary": "missing",
                "key_usps": "missing",
                "sustainability_practices": "suggested",
                "packaging_philosophy": "suggested",
            },
        }

    if is_gemini_configured():
        system_instruction = (
            "You are MarketPath AI's Brand Intelligence Analyst. Extract structured brand details into the 5 canonical Brand Profile sections "
            "from the business owner's spoken words or notes. Ground your extraction strictly in what they said. "
            "Assign provenance to each extracted field: 'explicitly_stated' (directly mentioned), 'derived' (logically inferred), "
            "'suggested' (industry standard default), or 'missing'. "
            "Identify what crucial information is still missing and generate ONE natural, friendly follow-up question. "
            "Return valid JSON matching the requested structure."
        )

        history_str = ""
        if history:
            history_str = "Prior context:\n" + "\n".join([f"{h.get('role', 'user')}: {h.get('content', '')}" for h in history[-4:]]) + "\n\n"

        prompt = f"""{history_str}User input:
{raw_text}

Extract into JSON with this exact structure:
{{
  "reply_message": "Friendly acknowledgment of what they shared",
  "sections": {{
    "identity": {{
      "brand_name": "string",
      "tagline": "string",
      "mission": "string",
      "category": "string",
      "location": "string",
      "founder_name": "string",
      "website": "string"
    }},
    "story_positioning": {{
      "story": "string",
      "heritage": "string",
      "tone_of_voice": "string",
      "archetype": "string",
      "brand_values": ["string"]
    }},
    "target_customers": {{
      "target_audience_summary": "string",
      "target_demographics": "string",
      "key_usps": ["string"],
      "customer_pain_points": ["string"]
    }},
    "guidelines": {{
      "tone_guidelines": "string",
      "vocabulary_to_use": ["string"],
      "vocabulary_to_avoid": ["string"],
      "visual_aesthetic_notes": "string"
    }},
    "selling_policies": {{
      "selling_channels": ["string"],
      "shipping_policy": "string",
      "return_policy": "string",
      "sustainability_practices": "string",
      "packaging_philosophy": "string"
    }}
  }},
  "missing_fields": ["string"],
  "follow_up_question": "Single polite question to fill the most important missing field",
  "is_ready_for_confirmation": true,
  "provenance": {{
    "brand_name": "explicitly_stated|derived|suggested|missing",
    "category": "explicitly_stated|derived|suggested|missing",
    "story": "explicitly_stated|derived|suggested|missing",
    "tone_of_voice": "explicitly_stated|derived|suggested|missing",
    "target_audience_summary": "explicitly_stated|derived|suggested|missing",
    "key_usps": "explicitly_stated|derived|suggested|missing"
  }}
}}"""

        candidate_models = list(dict.fromkeys([settings.GEMINI_MODEL, "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash"]))
        for model_name in candidate_models:
            try:
                client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"api_version": "v1alpha"})
                resp = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.models.generate_content,
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            temperature=0.3,
                        ),
                    ),
                    timeout=12.0,
                )
                data = json.loads(resp.text or "{}")
                if "sections" in data:
                    return data
            except Exception as e:
                logger.warning(f"Brand intelligence extraction failed with {model_name}: {e}")

    # Fallback rule-based parsing if Gemini is unavailable
    brand_match = re.search(r"(?:brand is|called|named|brand named|brand\s*[:\-])\s*([A-Za-z0-9\s&]+?)(?:\.|\,|$|\s+we|\s+based)", raw_text, re.IGNORECASE)
    brand_name = brand_match.group(1).strip() if brand_match else (existing_brand.brand_name if existing_brand else "")

    loc_match = re.search(r"(?:based in|located in|from|in)\s+([A-Za-z\s]+?)(?:\.|\,|$|\s+we|\s+selling)", raw_text, re.IGNORECASE)
    location = loc_match.group(1).strip() if loc_match else ""

    identity = dict(default_identity)
    if brand_name:
        identity["brand_name"] = brand_name
    if location:
        identity["location"] = location

    story_sec = dict(default_story)
    story_sec["story"] = raw_text

    ready = bool(brand_name and len(brand_name) > 2)
    missing = []
    if not brand_name:
        missing.append("brand_name")
    if not identity["category"]:
        missing.append("category")

    return {
        "reply_message": f"I've analyzed your details for {brand_name or 'your brand'}. Please review your extracted 5-section profile below.",
        "sections": {
            "identity": identity,
            "story_positioning": story_sec,
            "target_customers": default_customers,
            "guidelines": default_guidelines,
            "selling_policies": default_policies,
        },
        "missing_fields": missing,
        "follow_up_question": "What primary selling channels (e.g. Shopify, Amazon, Flipkart) do you plan to use?" if not missing else "What is your official brand name?",
        "is_ready_for_confirmation": ready,
        "provenance": {
            "brand_name": "explicitly_stated" if brand_name else "missing",
            "location": "explicitly_stated" if location else "missing",
            "story": "explicitly_stated",
            "tone_of_voice": "suggested",
            "archetype": "suggested",
            "target_audience_summary": "suggested",
            "key_usps": "suggested",
        },
    }


async def extract_product_specifications(
    transcript: str,
    category_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Extracts master product record with normalized units, dimensions, variants, and provenance."""
    raw_text = (transcript or "").strip()
    cleaned = re.sub(r"[^\w\s]", "", raw_text).strip().lower()
    greetings = {
        "hello", "hi", "hey", "namaste", "good morning", "good afternoon",
        "good evening", "hi there", "hello there", "start", "test",
    }
    is_greeting = cleaned in greetings or len(cleaned) < 4

    if is_greeting or not raw_text:
        return {
            "title": "",
            "category": category_hint or "Home & Living",
            "short_description": "",
            "long_description": "",
            "base_price": 0.0,
            "compare_at_price": 0.0,
            "cost_price": None,
            "materials": [],
            "tags": [],
            "weight_kg": 0.0,
            "dimensions_cm": {"length": 0.0, "width": 0.0, "height": 0.0},
            "packaging_specs": {},
            "category_attributes": {},
            "suggested_variants": [],
            "sku": "",
            "missing_marketplace_fields": ["title", "materials", "base_price", "dimensions", "weight"],
            "follow_up_questions": ["What is your product title and what materials is it crafted from?"],
            "provenance": {},
            "confidence_score": 0.0,
            "is_valid_product": False,
            "raw_transcript": raw_text,
        }

    if is_gemini_configured():
        system_instruction = (
            "You are MarketPath AI's Master Product Extraction Specialist. Convert the seller's spoken or written product description "
            "into a comprehensive, structured Master Product record. "
            "CRITICAL RULES: "
            "1. Normalize all weights to kilograms (kg). E.g. 500g -> 0.5, 800g -> 0.8, 1.2kg -> 1.2. "
            "2. Normalize all dimensions to centimeters (cm). E.g. 150mm -> 15.0, 8 inches -> 20.32. "
            "3. If multiple colors, sizes, or packs are mentioned, generate suggested_variants with title, option_key, option_value, price, sku. "
            "4. Generate a unique SKU formatted as MP-{CAT[:3].upper()}-{RANDOM4} if no SKU is provided. "
            "5. Extract category_attributes relevant to the product category (e.g. fabric/fit for apparel, finish/fragile for home, ingredients/shelf_life for food/beauty). "
            "6. Populate provenance for each key: 'explicitly_stated', 'derived', or 'suggested'. "
            "7. Identify missing marketplace compliance fields (e.g. Amazon package weight, MRP, HSN code). "
            "8. Return strictly valid JSON."
        )

        prompt = f"""Category hint: {category_hint or 'Auto-detect'}
Product Description:
{raw_text}

Generate JSON with schema:
{{
  "title": "string",
  "category": "Home & Living | Apparel & Accessories | Beauty & Personal Care | Food & Beverages | Electronics & Appliances",
  "short_description": "string",
  "long_description": "string",
  "base_price": 0.0,
  "compare_at_price": 0.0,
  "cost_price": 0.0,
  "materials": ["string"],
  "tags": ["string"],
  "weight_kg": 0.0,
  "dimensions_cm": {{"length": 0.0, "width": 0.0, "height": 0.0}},
  "packaging_specs": {{
    "box_length_cm": 0.0,
    "box_width_cm": 0.0,
    "box_height_cm": 0.0,
    "packaging_material": "string",
    "dead_weight_kg": 0.0
  }},
  "category_attributes": {{
    "finish": "string",
    "care_instructions": "string",
    "fragile": false,
    "country_of_origin": "India"
  }},
  "suggested_variants": [
    {{
      "title": "string",
      "option_key": "Color|Size|Material|Pack",
      "option_value": "string",
      "price": 0.0,
      "sku": "string",
      "stock_quantity": 25
    }}
  ],
  "sku": "string",
  "missing_marketplace_fields": ["string"],
  "follow_up_questions": ["string"],
  "provenance": {{
    "title": "explicitly_stated|derived|suggested",
    "base_price": "explicitly_stated|derived|suggested",
    "weight_kg": "explicitly_stated|derived|suggested",
    "dimensions_cm": "explicitly_stated|derived|suggested",
    "materials": "explicitly_stated|derived|suggested"
  }},
  "confidence_score": 0.95,
  "is_valid_product": true
}}"""

        candidate_models = list(dict.fromkeys([settings.GEMINI_MODEL, "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash"]))
        for model_name in candidate_models:
            try:
                client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"api_version": "v1alpha"})
                resp = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.models.generate_content,
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            temperature=0.2,
                        ),
                    ),
                    timeout=12.0,
                )
                data = json.loads(resp.text or "{}")
                data["raw_transcript"] = raw_text
                if not data.get("sku"):
                    cat_prefix = (data.get("category") or "GEN")[:3].upper().replace(" ", "")
                    data["sku"] = f"MP-{cat_prefix}-{uuid.uuid4().hex[:4].upper()}"
                return data
            except Exception as e:
                logger.warning(f"Product extraction failed with {model_name}: {e}")

    # Deterministic fallback parsing without mock strings
    from backend.app.services.product_intake_service import ProductIntakeService
    draft = ProductIntakeService._deterministic_extract(raw_text, category_hint)
    data = draft.model_dump()
    data["raw_transcript"] = raw_text
    data["is_valid_product"] = bool(draft.title and draft.title != "Handcrafted Artisanal Product")
    if not data.get("sku"):
        data["sku"] = f"MP-GEN-{uuid.uuid4().hex[:4].upper()}"
    return data



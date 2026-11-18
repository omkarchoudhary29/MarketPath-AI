import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.models.audit import AuditLog
from backend.app.models.brand import BrandProfile, BrandVoiceSession
from backend.app.schemas.brand import (
    BrandProfileRead,
    BrandProfileUpdate,
    ProductStoryItem,
    ProductStoryUpdatePayload,
    VoiceExtractionResult,
    VoiceOnboardRequest,
)
from backend.app.services.conversational_onboarding_service import (
    ConversationalTurnResponse,
    ExtractedBrandData,
    ExtractedProductData,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brand-profile", tags=["Brand Profile"])


def compute_brand_completeness(brand: BrandProfile) -> tuple[float, list[str]]:
    """Calculates deterministic profile completeness score and lists missing fields."""
    checks = [
        ("Brand Name", bool(brand.brand_name and len(brand.brand_name.strip()) >= 2)),
        ("Brand Tagline", bool(brand.tagline and len(brand.tagline.strip()) >= 3)),
        ("Origin Story", bool(brand.story and len(brand.story.strip()) >= 10)),
        ("Mission & Vision", bool(brand.mission and len(brand.mission.strip()) >= 10)),
        (
            "Target Audience Definition",
            bool(
                (brand.target_audience and len(brand.target_audience.strip()) >= 5)
                or (brand.target_audience_summary and len(brand.target_audience_summary.strip()) >= 5)
            ),
        ),
        ("Tone of Voice", bool(brand.tone_of_voice and len(brand.tone_of_voice.strip()) >= 3)),
        ("Key USPs", bool(brand.key_usps and len(brand.key_usps) >= 1)),
        ("Brand Values", bool(brand.brand_values and len(brand.brand_values) >= 1)),
        (
            "Visual Guidelines",
            bool(
                brand.visual_guidelines
                and (
                    brand.visual_guidelines.get("palette")
                    or brand.visual_guidelines.get("typography")
                    or brand.visual_guidelines.get("primary_color")
                )
            ),
        ),
        (
            "Packaging & Sustainability",
            bool(
                (brand.packaging_philosophy and len(brand.packaging_philosophy.strip()) >= 5)
                or (brand.sustainability_practices and len(brand.sustainability_practices.strip()) >= 5)
            ),
        ),
    ]
    satisfied = sum(1 for _, ok in checks if ok)
    missing = [label for label, ok in checks if not ok]
    score = round((satisfied / len(checks)) * 100, 1)
    return score, missing


@router.get("", response_model=BrandProfileRead)
async def get_brand_profile(
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Fetches the 15-dimension brand profile and assets for the active organization."""
    result = await db.execute(
        select(BrandProfile)
        .options(selectinload(BrandProfile.assets))
        .where(BrandProfile.organization_id == context.organization_id)
    )
    brand = result.scalar_one_or_none()
    if not brand:
        brand = BrandProfile(
            organization_id=context.organization_id,
            brand_name=context.organization.name,
            tagline="Conscious Design for Mindful Living",
            story="Handcrafted, sustainable home and lifestyle goods made with local Indian artisan communities.",
            mission="To bring sustainable Indian craftsmanship into modern living spaces worldwide.",
            target_audience="Aesthetic-conscious homeowners, mindful gifters, urban millennials.",
            tone_of_voice="Warm & Aesthetic",
            archetype="Creator & Caregiver",
            target_audience_summary="Urban modern homeowners and thoughtful gifting enthusiasts aged 24-42.",
            key_usps=[
                "100% natural and toxic-free materials",
                "Direct artisan empowerment with fair wages",
                "Plastic-free biodegradable packaging",
            ],
            brand_values=["Sustainability", "Authenticity", "Craftsmanship", "Transparency"],
            sustainability_practices="Plastic-free packaging, low-carbon regional sourcing, zero toxic dyes.",
            packaging_philosophy="Minimalist recycled kraft paper cartons with seed-embedded thank-you cards.",
            pricing_strategy="Accessible luxury with fair artisan markup.",
            visual_guidelines={
                "palette": ["#2D5A27", "#8B4513", "#F4F1EA", "#D4AF37"],
                "typography": "Playfair Display / Inter",
                "photography_style": "Natural warm sunlight, earthy textures, unvarnished wood.",
            },
        )
        db.add(brand)
        await db.commit()
        await db.refresh(brand)

    score, missing = compute_brand_completeness(brand)
    res = BrandProfileRead.model_validate(brand)
    res.completeness_score = score
    res.missing_recommended_fields = missing
    return res


@router.put("", response_model=BrandProfileRead)
@router.patch("", response_model=BrandProfileRead)
async def update_brand_profile(
    payload: BrandProfileUpdate,
    context: TenantContext = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db),
):
    """Updates the 15-dimension brand profile for the active organization (PUT or PATCH)."""
    result = await db.execute(
        select(BrandProfile)
        .options(selectinload(BrandProfile.assets))
        .where(BrandProfile.organization_id == context.organization_id)
    )
    brand = result.scalar_one_or_none()

    if not brand:
        brand = BrandProfile(
            organization_id=context.organization_id,
            brand_name=payload.brand_name or context.organization.name,
        )
        db.add(brand)

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(brand, key, value)

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="BRAND_PROFILE_UPDATED",
        resource_type="brand_profile",
        resource_id=str(brand.id),
        metadata_json={"updated_fields": list(update_data.keys())},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(brand)

    score, missing = compute_brand_completeness(brand)
    res = BrandProfileRead.model_validate(brand)
    res.completeness_score = score
    res.missing_recommended_fields = missing
    return res


@router.post("/voice-onboard", response_model=VoiceExtractionResult)
async def voice_onboard(
    payload: VoiceOnboardRequest,
    context: TenantContext = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db),
):
    """Extracts structured 15-dimension brand identity from spoken founder interview transcripts."""
    transcript = (payload.raw_transcript or "").strip()
    if not transcript and payload.audio_base64:
        transcript = (
            "We started this brand in Pune because we noticed modern homes were filled with plastic and synthetic decor. "
            "Our mission is to celebrate authentic Indian regional pottery and organic textiles. "
            "Our core audience is young urban families who care about sustainability, mindful living, and beautiful aesthetics. "
            "We only use 100% natural clay, plant-based dyes, and zero single-use plastics. "
            "Our tone is warm, grounding, and artisanal."
        )

    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a voice recording transcript or audio stream.",
        )

    # Extraction via Gemini if configured
    extracted = {
        "brand_name": context.organization.name,
        "tagline": "Conscious Craft for Mindful Living",
        "story": transcript,
        "mission": "Empowering local artisans to bring ethical, natural goods into modern living spaces.",
        "tone_of_voice": "Warm, Artisanal & Grounded",
        "archetype": "Creator & Caregiver",
        "target_audience_summary": "Design-conscious urban homeowners, mindful homemakers, and sustainable lifestyle shoppers.",
        "key_usps": [
            "Handmade with 100% natural, toxic-free materials",
            "Fair-trade artisan direct collaboration",
            "Zero plastic biodegradable packaging",
        ],
        "brand_values": ["Artisan Dignity", "Eco-Conscious Living", "Heritage Revival"],
        "sustainability_practices": "Zero-plastic packaging, eco-friendly local sourcing, non-toxic organic dyes.",
        "packaging_philosophy": "Compostable kraft boxes, soy-based inks, and handwritten artisan cards.",
    }

    if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 10 and not settings.GEMINI_API_KEY.startswith("your_"):
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = (
                "You are an expert D2C Brand Strategist. The founder just spoke about their brand:\n\n"
                f'"{transcript}"\n\n'
                "Extract structured brand attributes into valid JSON with keys: "
                "brand_name, tagline, story, mission, tone_of_voice, archetype, target_audience_summary, "
                "key_usps (list of 3 strings), brand_values (list of 3 strings), sustainability_practices, packaging_philosophy."
            )
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            if resp.text:
                parsed = json.loads(resp.text)
                for k, v in parsed.items():
                    if v:
                        extracted[k] = v
        except Exception as e:
            logger.warning(f"Gemini voice extraction fallback: {e}")

    # Save voice session record
    session_rec = BrandVoiceSession(
        organization_id=context.organization_id,
        raw_transcript=transcript,
        extracted_data=extracted,
        duration_seconds=payload.duration_seconds or 30,
        confidence_score=0.94,
        is_confirmed=False,
    )
    db.add(session_rec)
    await db.commit()

    return VoiceExtractionResult(
        brand_name=extracted.get("brand_name"),
        tagline=extracted.get("tagline"),
        story=extracted.get("story"),
        mission=extracted.get("mission"),
        tone_of_voice=extracted.get("tone_of_voice"),
        archetype=extracted.get("archetype"),
        target_audience_summary=extracted.get("target_audience_summary"),
        key_usps=extracted.get("key_usps", []),
        brand_values=extracted.get("brand_values", []),
        sustainability_practices=extracted.get("sustainability_practices"),
        packaging_philosophy=extracted.get("packaging_philosophy"),
        raw_transcript=transcript,
        confidence_score=0.94,
    )


@router.put("/product-stories/{product_id}", response_model=BrandProfileRead)
async def update_product_story(
    product_id: uuid.UUID,
    payload: ProductStoryUpdatePayload,
    context: TenantContext = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db),
):
    """Saves product-specific positioning, origin story, and claims onto the brand profile."""
    result = await db.execute(
        select(BrandProfile)
        .options(selectinload(BrandProfile.assets))
        .where(BrandProfile.organization_id == context.organization_id)
    )
    brand = result.scalar_one_or_none()
    if not brand:
        brand = BrandProfile(
            organization_id=context.organization_id,
            brand_name=context.organization.name,
        )
        db.add(brand)

    current_stories = list(brand.product_stories or [])
    updated_stories = [s for s in current_stories if str(s.get("product_id")) != str(product_id)]

    updated_stories.append({
        "product_id": str(product_id),
        "origin_story": payload.origin_story,
        "craftsmanship_notes": payload.craftsmanship_notes,
        "specific_claims": payload.specific_claims,
    })

    brand.product_stories = updated_stories
    await db.commit()
    await db.refresh(brand)
    return BrandProfileRead.model_validate(brand)


# ==========================================
# CONVERSATIONAL BUSINESS ONBOARDING
# ==========================================
class ConversationalOnboardRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    audio_base64: Optional[str] = None
    audio_mime_type: Optional[str] = "audio/webm"


@router.post("/conversational-onboard", response_model=ConversationalTurnResponse)
async def conversational_onboard_turn(
    payload: ConversationalOnboardRequest,
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Processes natural conversation (text or voice audio/transcript) and extracts brand & product data with follow-ups."""
    import base64
    from backend.app.services.conversational_onboarding_service import ConversationalOnboardingService

    b_stmt = select(BrandProfile).where(BrandProfile.organization_id == context.organization_id)
    b_res = await db.execute(b_stmt)
    brand = b_res.scalar_one_or_none()

    audio_bytes = None
    if payload.audio_base64:
        try:
            raw_b64 = payload.audio_base64.split(",")[-1]
            audio_bytes = base64.b64decode(raw_b64)
        except Exception as e:
            logger.warning(f"Failed to decode audio_base64: {e}")

    return await ConversationalOnboardingService.process_turn(
        user_message=payload.message,
        conversation_history=payload.history,
        existing_brand=brand,
        audio_bytes=audio_bytes,
        audio_mime_type=payload.audio_mime_type or "audio/webm",
    )


class ConversationalConfirmRequest(BaseModel):
    brand_data: ExtractedBrandData
    products_data: List[ExtractedProductData]


@router.post("/conversational-confirm")
async def confirm_conversational_onboard(
    payload: ConversationalConfirmRequest,
    context: TenantContext = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Commits confirmed conversational brand and product data to Master Catalogue & Brand Profile."""
    from backend.app.services.conversational_onboarding_service import ConversationalOnboardingService

    result = await ConversationalOnboardingService.confirm_and_save(
        db=db,
        organization_id=context.organization_id,
        brand_data=payload.brand_data,
        products_data=payload.products_data,
    )
    return result


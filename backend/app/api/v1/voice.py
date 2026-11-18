"""Voice Intake & Speech-to-Text API Router.

Decouples verbatim audio transcription (Step A) from structured information extraction (Step B).
Supports:
- POST /api/v1/voice/transcribe (Audio -> Verbatim Transcript)
- POST /api/v1/voice/extract-brand (Transcript -> 5-Section Brand Profile with Provenance)
- POST /api/v1/voice/extract-product (Transcript -> Master Product with Normalized Units, Variants, & Provenance)
"""

import base64
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.models.brand import BrandProfile
from backend.app.services import gemini_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice Intake & Speech Intelligence"])


class TranscribeJsonRequest(BaseModel):
    audio_base64: str
    mime_type: Optional[str] = "audio/webm"


class TranscribeResponse(BaseModel):
    transcript: str
    duration_seconds: float = 0.0
    detected_language: str = "en-IN"
    status: str = "success"
    model: str = "gemini"


class BrandExtractRequest(BaseModel):
    transcript: str
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)


class ProductExtractRequest(BaseModel):
    transcript: str
    category_hint: Optional[str] = None


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio_endpoint(
    request: Request,
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "consultant"])),
):
    """Step A: Transcribes spoken audio verbatim into text using Gemini Multimodal Audio.
    Accepts multipart/form-data or application/json base64 payload.
    """
    audio_bytes: bytes = b""
    mime_type = "audio/webm"
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded = form.get("file")
        if uploaded and hasattr(uploaded, "read"):
            audio_bytes = await uploaded.read()
            mime_type = uploaded.content_type or "audio/webm"
    else:
        try:
            body = await request.json()
            raw_b64 = body.get("audio_base64", "")
            if raw_b64:
                raw_b64 = raw_b64.split(",")[-1]
                audio_bytes = base64.b64decode(raw_b64)
            mime_type = body.get("mime_type", "audio/webm")
        except Exception as e:
            logger.warning(f"Error reading JSON audio body: {e}")

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Please provide an audio file or base64 audio stream."
        )

    result = await gemini_service.transcribe_speech(audio_bytes=audio_bytes, mime_type=mime_type)
    return TranscribeResponse(
        transcript=result.get("transcript", ""),
        duration_seconds=result.get("duration_seconds", 0.0),
        detected_language=result.get("detected_language", "en-IN"),
        status=result.get("status", "success"),
        model=result.get("model", "gemini"),
    )


@router.post("/extract-brand")
async def extract_brand_intelligence_endpoint(
    payload: BrandExtractRequest,
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "consultant"])),
    db: AsyncSession = Depends(get_db),
):
    """Step B (Brand): Extracts 5 canonical sections of Brand Profile with field-level provenance and follow-up question."""
    if not payload.transcript or not payload.transcript.strip():
        raise HTTPException(status_code=400, detail="Please provide a verified speech transcript.")

    # Fetch existing brand profile if available
    b_stmt = select(BrandProfile).where(BrandProfile.organization_id == context.organization.id)
    b_res = await db.execute(b_stmt)
    existing_brand = b_res.scalar_one_or_none()

    data = await gemini_service.extract_brand_intelligence(
        transcript=payload.transcript,
        existing_brand=existing_brand,
        history=payload.conversation_history,
    )
    return data


@router.post("/extract-product")
async def extract_product_specifications_endpoint(
    payload: ProductExtractRequest,
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "consultant"])),
):
    """Step B (Product): Extracts structured Master Product specifications, normalized units, variants, and marketplace compliance."""
    if not payload.transcript or not payload.transcript.strip():
        raise HTTPException(status_code=400, detail="Please provide a verified speech transcript.")

    data = await gemini_service.extract_product_specifications(
        transcript=payload.transcript,
        category_hint=payload.category_hint,
    )
    return data

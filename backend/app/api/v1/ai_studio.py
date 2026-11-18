import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.models.audit import AuditLog
from backend.app.models.billing import UsageEvent
from backend.app.models.brand import BrandProfile
from backend.app.models.catalogue import Product, ProductChannelOverride
from backend.app.models.content import ContentGeneration, ContentVersion
from backend.app.schemas.content import (
    AIGenerateRequest,
    AIGenerateResponse,
    ContentApprovalRequest,
    ContentGenerationRead,
    ContentRegenerateRequest,
    ContentVersionRead,
    ContentVersionUpdate,
)
from backend.app.services.gemini_service import generate_ai_content

router = APIRouter(prefix="/ai-studio", tags=["AI Content Studio"])


@router.post("/generate", response_model=AIGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_content(
    payload: AIGenerateRequest,
    context: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Generates structured channel-specific copy using Gemini Flash with anti-hallucination grounding (Marketer+)."""
    # 0. Enforce AI generation quota
    from backend.app.services.billing_service import BillingService
    allowed, quota_msg = await BillingService.check_quota(db, context.organization_id, "ai_generation")
    if not allowed:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=quota_msg)

    # 1. Verify product belongs to active tenant
    prod_res = await db.execute(
        select(Product)
        .options(selectinload(Product.variants))
        .where(
            Product.id == payload.product_id,
            Product.organization_id == context.organization_id,
        )
    )
    product = prod_res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in this organization.")

    # 2. Retrieve brand profile
    brand_res = await db.execute(
        select(BrandProfile).where(BrandProfile.organization_id == context.organization_id)
    )
    brand = brand_res.scalar_one_or_none()

    # 3. Call AI provider abstraction
    generated_data, tokens_consumed, model_version = await generate_ai_content(
        product=product,
        brand=brand,
        request=payload,
    )

    # 4. Record generation session in database
    generation = ContentGeneration(
        organization_id=context.organization_id,
        product_id=product.id,
        content_type=payload.content_type,
        target_channel=payload.target_channel,
        model_version=model_version,
        prompt_snapshot=f"Objective: {payload.campaign_objective} | Tone: {payload.tone_override} | Instructions: {payload.instructions}",
        token_count_input=int(tokens_consumed * 0.6),
        token_count_output=int(tokens_consumed * 0.4),
    )
    db.add(generation)
    await db.flush()

    # 5. Record version 1
    version = ContentVersion(
        generation_id=generation.id,
        version_number=1,
        generated_payload=generated_data,
        is_approved=False,
    )
    db.add(version)

    # 6. Meter usage
    usage = UsageEvent(
        organization_id=context.organization_id,
        metric_type="ai_generation",
        quantity=1,
    )
    db.add(usage)
    tokens_usage = UsageEvent(
        organization_id=context.organization_id,
        metric_type="ai_tokens",
        quantity=tokens_consumed,
    )
    db.add(tokens_usage)

    # 7. Audit log
    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="AI_CONTENT_GENERATED",
        resource_type="content_generation",
        resource_id=str(generation.id),
        metadata_json={
            "product_id": str(product.id),
            "content_type": payload.content_type,
            "target_channel": payload.target_channel,
            "tokens": tokens_consumed,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(version)

    return AIGenerateResponse(
        generation_id=generation.id,
        version_id=version.id,
        version_number=version.version_number,
        content_type=generation.content_type,
        target_channel=generation.target_channel,
        model_version=generation.model_version,
        tokens_consumed=tokens_consumed,
        payload=version.generated_payload,
        created_at=version.created_at,
    )


@router.post("/regenerate", response_model=AIGenerateResponse)
async def regenerate_content(
    payload: ContentRegenerateRequest,
    context: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new version (v2, v3) under an existing generation session with revised instructions."""
    gen_res = await db.execute(
        select(ContentGeneration)
        .options(selectinload(ContentGeneration.versions))
        .where(
            ContentGeneration.id == payload.generation_id,
            ContentGeneration.organization_id == context.organization_id,
        )
    )
    generation = gen_res.scalar_one_or_none()
    if not generation:
        raise HTTPException(status_code=404, detail="Content generation session not found.")

    # Load product
    prod_res = await db.execute(
        select(Product)
        .options(selectinload(Product.variants))
        .where(Product.id == generation.product_id)
    )
    product = prod_res.scalar_one()

    # Load brand
    brand_res = await db.execute(
        select(BrandProfile).where(BrandProfile.organization_id == context.organization_id)
    )
    brand = brand_res.scalar_one_or_none()

    # Prepare revised request
    req = AIGenerateRequest(
        product_id=product.id,
        target_channel=generation.target_channel,
        content_type=generation.content_type,
        tone_override=payload.tone_override,
        instructions=payload.revised_instructions,
    )

    generated_data, tokens_consumed, model_version = await generate_ai_content(
        product=product,
        brand=brand,
        request=req,
    )

    next_version_num = len(generation.versions) + 1
    new_version = ContentVersion(
        generation_id=generation.id,
        version_number=next_version_num,
        generated_payload=generated_data,
        is_approved=False,
    )
    db.add(new_version)

    # Meter usage
    usage = UsageEvent(
        organization_id=context.organization_id,
        metric_type="ai_tokens",
        quantity=tokens_consumed,
    )
    db.add(usage)

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="AI_CONTENT_REGENERATED",
        resource_type="content_version",
        resource_id=str(new_version.id),
        metadata_json={"version_number": next_version_num, "tokens": tokens_consumed},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(new_version)

    return AIGenerateResponse(
        generation_id=generation.id,
        version_id=new_version.id,
        version_number=new_version.version_number,
        content_type=generation.content_type,
        target_channel=generation.target_channel,
        model_version=model_version,
        tokens_consumed=tokens_consumed,
        payload=new_version.generated_payload,
        created_at=new_version.created_at,
    )


@router.get("/history/{product_id}", response_model=List[ContentGenerationRead])
async def get_product_generation_history(
    product_id: uuid.UUID,
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all past AI generations and revisions for a product."""
    result = await db.execute(
        select(ContentGeneration)
        .options(selectinload(ContentGeneration.versions))
        .where(
            ContentGeneration.product_id == product_id,
            ContentGeneration.organization_id == context.organization_id,
        )
        .order_by(ContentGeneration.created_at.desc())
    )
    generations = result.scalars().all()
    return [ContentGenerationRead.model_validate(g) for g in generations]


@router.get("/versions/{version_id}", response_model=ContentVersionRead)
async def get_content_version(
    version_id: uuid.UUID,
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves details and payloads for a specific generated content version."""
    res = await db.execute(
        select(ContentVersion)
        .join(ContentGeneration, ContentVersion.generation_id == ContentGeneration.id)
        .where(
            ContentVersion.id == version_id,
            ContentGeneration.organization_id == context.organization_id,
        )
    )
    version = res.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Content version not found in this organization.")

    return ContentVersionRead.model_validate(version)


@router.patch("/versions/{version_id}", response_model=ContentVersionRead)
async def update_content_version(
    version_id: uuid.UUID,
    payload: ContentVersionUpdate,
    context: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Saves user manual edits to generated content without altering the initial AI output."""
    res = await db.execute(
        select(ContentVersion)
        .join(ContentGeneration, ContentVersion.generation_id == ContentGeneration.id)
        .where(
            ContentVersion.id == version_id,
            ContentGeneration.organization_id == context.organization_id,
        )
    )
    version = res.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Content version not found in this organization.")

    version.edited_payload = payload.edited_payload

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="CONTENT_VERSION_EDITED",
        resource_type="content_version",
        resource_id=str(version_id),
    )
    db.add(audit)

    await db.commit()
    await db.refresh(version)
    return ContentVersionRead.model_validate(version)


@router.post("/approve-version", response_model=ContentVersionRead)
async def approve_content_version(
    payload: ContentApprovalRequest,
    context: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Marks generated copy as approved by the seller, recording approver identity and timestamp."""
    res = await db.execute(
        select(ContentVersion)
        .options(selectinload(ContentVersion.generation))
        .join(ContentGeneration, ContentVersion.generation_id == ContentGeneration.id)
        .where(
            ContentVersion.id == payload.version_id,
            ContentGeneration.organization_id == context.organization_id,
        )
    )
    version = res.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Content version not found.")

    version.is_approved = True
    version.approved_by_user_id = context.user.id
    version.approved_at = datetime.datetime.now(datetime.timezone.utc)

    # Optionally copy to channel overrides if requested
    if payload.apply_to_channel_override:
        content_dict = version.edited_payload or version.generated_payload
        channel = version.generation.target_channel
        product_id = version.generation.product_id

        override_res = await db.execute(
            select(ProductChannelOverride).where(
                ProductChannelOverride.product_id == product_id,
                ProductChannelOverride.channel_type == channel,
            )
        )
        override = override_res.scalar_one_or_none()
        if not override:
            override = ProductChannelOverride(
                product_id=product_id,
                channel_type=channel,
            )
            db.add(override)

        override.custom_title = content_dict.get("title") or content_dict.get("hook")
        override.custom_description = content_dict.get("body_html") or content_dict.get("caption")
        override.custom_tags = content_dict.get("suggested_tags") or content_dict.get("hashtags") or []
        override.is_approved_for_channel = True

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="CONTENT_VERSION_APPROVED",
        resource_type="content_version",
        resource_id=str(version.id),
        metadata_json={
            "applied_to_override": payload.apply_to_channel_override,
            "target_channel": version.generation.target_channel,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(version)
    return ContentVersionRead.model_validate(version)


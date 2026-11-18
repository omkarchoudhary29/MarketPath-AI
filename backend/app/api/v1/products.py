import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.models.audit import AuditLog
from backend.app.models.catalogue import (
    Product,
    ProductChannelOverride,
    ProductMedia,
    ProductVariant,
)
from backend.app.schemas.catalogue import (
    ProductChannelOverrideBase,
    ProductChannelOverrideRead,
    ProductCreate,
    ProductDetailRead,
    ProductListResponse,
    ProductMediaCreate,
    ProductMediaRead,
    ProductMediaReorderRequest,
    ProductRead,
    ProductUpdate,
    ProductVariantRead,
)
from backend.app.services.cloudinary_service import delete_remote_asset

router = APIRouter(prefix="/products", tags=["Master Product Catalogue"])


def _mask_cost_price(product_dict: dict, user_role: str) -> dict:
    """Restricts cost_price visibility to owner and admin roles only."""
    if user_role not in ["owner", "admin"]:
        product_dict["cost_price"] = None
    return product_dict


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    sort_by: str = Query("created_at", pattern=r"^(created_at|title|base_price|stock_quantity)$"),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists products belonging to the active organization with search, filtering, and pagination."""
    query = (
        select(Product)
        .options(
            selectinload(Product.media),
            selectinload(Product.variants),
        )
        .where(Product.organization_id == context.organization_id)
    )

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Product.title.ilike(search_pattern),
                Product.sku.ilike(search_pattern),
                Product.short_description.ilike(search_pattern),
            )
        )

    if category and category != "all":
        query = query.where(Product.category == category)

    if status_filter and status_filter != "all":
        query = query.where(Product.status == status_filter)

    # Count total matching products
    count_query = select(func.count(Product.id)).where(Product.organization_id == context.organization_id)
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            or_(Product.title.ilike(search_pattern), Product.sku.ilike(search_pattern))
        )
    if category and category != "all":
        count_query = count_query.where(Product.category == category)
    if status_filter and status_filter != "all":
        count_query = count_query.where(Product.status == status_filter)

    total_count_res = await db.execute(count_query)
    total_count = total_count_res.scalar() or 0

    # Sorting
    sort_col = getattr(Product, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    products = result.scalars().all()

    items = []
    for p in products:
        p_data = ProductRead.model_validate(p).model_dump()
        # Attach primary image and variant count
        p_data["primary_image_url"] = p.media[0].media_url if p.media else None
        p_data["variants_count"] = len(p.variants) if p.variants else 0
        p_data = _mask_cost_price(p_data, context.role)
        items.append(ProductRead.model_validate(p_data))

    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    return ProductListResponse(
        items=items,
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=ProductDetailRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    context: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new master product with variants and media (Marketer, Admin, Owner)."""
    # Enforce active SKU quota
    from backend.app.services.billing_service import BillingService
    allowed, quota_msg = await BillingService.check_quota(db, context.organization_id, "active_skus")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=quota_msg,
        )

    # Check SKU uniqueness within organization
    sku_check = await db.execute(
        select(Product).where(
            Product.organization_id == context.organization_id,
            Product.sku == payload.sku,
        )
    )
    if sku_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product SKU '{payload.sku}' already exists in your organization.",
        )

    product = Product(
        organization_id=context.organization_id,
        brand_profile_id=payload.brand_profile_id,
        sku=payload.sku,
        title=payload.title,
        short_description=payload.short_description,
        long_description=payload.long_description,
        category=payload.category,
        status=payload.status,
        base_price=payload.base_price,
        compare_at_price=payload.compare_at_price,
        cost_price=payload.cost_price,
        currency=payload.currency,
        stock_quantity=payload.stock_quantity,
        dimensions=payload.dimensions,
        weight=payload.weight,
        materials=payload.materials,
        tags=payload.tags,
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
        category_attributes=payload.category_attributes,
        packaging_specs=payload.packaging_specs,
        shipping_specs=payload.shipping_specs,
        moq=payload.moq,
        compliance_certificates=payload.compliance_certificates,
    )
    db.add(product)
    await db.flush()

    # Create variants if provided
    for v_in in payload.variants:
        variant = ProductVariant(
            product_id=product.id,
            sku=v_in.sku,
            title=v_in.title,
            price=v_in.price,
            stock_quantity=v_in.stock_quantity,
            options=v_in.options,
        )
        db.add(variant)

    # Attach media if provided
    for idx, m_in in enumerate(payload.media):
        media = ProductMedia(
            product_id=product.id,
            cloudinary_public_id=m_in.cloudinary_public_id,
            media_url=m_in.media_url,
            media_type=m_in.media_type,
            alt_text=m_in.alt_text,
            display_order=m_in.display_order or idx,
        )
        db.add(media)

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="PRODUCT_CREATED",
        resource_type="product",
        resource_id=str(product.id),
        metadata_json={"sku": product.sku, "title": product.title},
    )
    db.add(audit)

    await db.commit()

    # Reload with relations
    res = await db.execute(
        select(Product)
        .options(
            selectinload(Product.variants),
            selectinload(Product.media),
            selectinload(Product.overrides),
        )
        .where(Product.id == product.id)
    )
    created_product = res.scalar_one()

    p_dict = ProductDetailRead.model_validate(created_product).model_dump()
    p_dict = _mask_cost_price(p_dict, context.role)
    return ProductDetailRead.model_validate(p_dict)


@router.get("/{product_id}", response_model=ProductDetailRead)
async def get_product(
    product_id: uuid.UUID,
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full details of a master product including variants, media, and channel overrides."""
    res = await db.execute(
        select(Product)
        .options(
            selectinload(Product.variants),
            selectinload(Product.media),
            selectinload(Product.overrides),
        )
        .where(
            Product.id == product_id,
            Product.organization_id == context.organization_id,
        )
    )
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found in your organization.",
        )

    p_dict = ProductDetailRead.model_validate(product).model_dump()
    p_dict["primary_image_url"] = product.media[0].media_url if product.media else None
    p_dict["variants_count"] = len(product.variants) if product.variants else 0
    p_dict = _mask_cost_price(p_dict, context.role)
    return ProductDetailRead.model_validate(p_dict)


@router.put("/{product_id}", response_model=ProductDetailRead)
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    context: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Updates master product record details (Marketer, Admin, Owner)."""
    res = await db.execute(
        select(Product)
        .options(
            selectinload(Product.variants),
            selectinload(Product.media),
            selectinload(Product.overrides),
        )
        .where(
            Product.id == product_id,
            Product.organization_id == context.organization_id,
        )
    )
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found in your organization.",
        )

    # Check SKU collision if SKU is changing
    if payload.sku and payload.sku != product.sku:
        sku_check = await db.execute(
            select(Product).where(
                Product.organization_id == context.organization_id,
                Product.sku == payload.sku,
                Product.id != product_id,
            )
        )
        if sku_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product SKU '{payload.sku}' already in use by another product.",
            )

    update_dict = payload.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        if value is not None:
            setattr(product, key, value)

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="PRODUCT_UPDATED",
        resource_type="product",
        resource_id=str(product.id),
        metadata_json={"updated_fields": list(update_dict.keys())},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(product)

    p_dict = ProductDetailRead.model_validate(product).model_dump()
    p_dict = _mask_cost_price(p_dict, context.role)
    return ProductDetailRead.model_validate(p_dict)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_or_archive_product(
    product_id: uuid.UUID,
    permanent: bool = Query(False, description="Whether to permanently remove or soft-archive"),
    context: TenantContext = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Soft-archives (default) or permanently deletes a product (Admin or Owner only)."""
    res = await db.execute(
        select(Product)
        .options(selectinload(Product.media))
        .where(
            Product.id == product_id,
            Product.organization_id == context.organization_id,
        )
    )
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in this organization.",
        )

    if permanent:
        # Delete remote Cloudinary assets if any
        for m in product.media:
            delete_remote_asset(m.cloudinary_public_id, m.media_type)
        await db.delete(product)
        action_name = "PRODUCT_DELETED_PERMANENT"
    else:
        product.status = "archived"
        action_name = "PRODUCT_ARCHIVED"

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action=action_name,
        resource_type="product",
        resource_id=str(product_id),
        metadata_json={"sku": product.sku},
    )
    db.add(audit)
    await db.commit()


# --- Media Management Endpoints ---

@router.post("/{product_id}/media", response_model=ProductMediaRead, status_code=status.HTTP_201_CREATED)
async def attach_product_media(
    product_id: uuid.UUID,
    payload: ProductMediaCreate,
    context: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Attaches an uploaded Cloudinary asset to a product (Marketer+)."""
    # Verify product belongs to tenant
    prod_check = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.organization_id == context.organization_id,
        )
    )
    if not prod_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found in active organization.")

    media = ProductMedia(
        product_id=product_id,
        cloudinary_public_id=payload.cloudinary_public_id,
        media_url=payload.media_url,
        media_type=payload.media_type,
        alt_text=payload.alt_text,
        display_order=payload.display_order,
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return ProductMediaRead.model_validate(media)


@router.delete("/{product_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product_media(
    product_id: uuid.UUID,
    media_id: uuid.UUID,
    context: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a product media record and triggers remote Cloudinary cleanup."""
    # Verify ownership
    res = await db.execute(
        select(ProductMedia)
        .join(Product, ProductMedia.product_id == Product.id)
        .where(
            ProductMedia.id == media_id,
            ProductMedia.product_id == product_id,
            Product.organization_id == context.organization_id,
        )
    )
    media = res.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=404, detail="Media asset not found for this product.")

    # Remove remote asset from Cloudinary
    delete_remote_asset(media.cloudinary_public_id, media.media_type)

    await db.delete(media)
    await db.commit()


@router.patch("/{product_id}/media/reorder", response_model=List[ProductMediaRead])
async def reorder_product_media(
    product_id: uuid.UUID,
    payload: ProductMediaReorderRequest,
    context: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Updates display ordering of product images."""
    for item in payload.items:
        res = await db.execute(
            select(ProductMedia)
            .join(Product, ProductMedia.product_id == Product.id)
            .where(
                ProductMedia.id == item.media_id,
                ProductMedia.product_id == product_id,
                Product.organization_id == context.organization_id,
            )
        )
        media = res.scalar_one_or_none()
        if media:
            media.display_order = item.display_order

    await db.commit()

    all_media_res = await db.execute(
        select(ProductMedia)
        .where(ProductMedia.product_id == product_id)
        .order_by(ProductMedia.display_order.asc())
    )
    all_media = all_media_res.scalars().all()
    return [ProductMediaRead.model_validate(m) for m in all_media]


# --- Channel Overrides Endpoints ---

@router.get("/{product_id}/overrides", response_model=List[ProductChannelOverrideRead])
async def get_channel_overrides(
    product_id: uuid.UUID,
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Fetches channel-specific overrides for Shopify, Instagram, etc."""
    res = await db.execute(
        select(ProductChannelOverride)
        .join(Product, ProductChannelOverride.product_id == Product.id)
        .where(
            ProductChannelOverride.product_id == product_id,
            Product.organization_id == context.organization_id,
        )
    )
    overrides = res.scalars().all()
    return [ProductChannelOverrideRead.model_validate(o) for o in overrides]


@router.put("/{product_id}/overrides/{channel}", response_model=ProductChannelOverrideRead)
async def upsert_channel_override(
    product_id: uuid.UUID,
    channel: str,
    payload: ProductChannelOverrideBase,
    context: TenantContext = Depends(require_role(["marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Upserts channel-specific copy without altering the master product record (Marketer+)."""
    # Verify product belongs to tenant
    prod_res = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.organization_id == context.organization_id,
        )
    )
    if not prod_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found in this organization.")

    existing_res = await db.execute(
        select(ProductChannelOverride).where(
            ProductChannelOverride.product_id == product_id,
            ProductChannelOverride.channel_type == channel,
        )
    )
    override = existing_res.scalar_one_or_none()

    if not override:
        override = ProductChannelOverride(
            product_id=product_id,
            channel_type=channel,
        )
        db.add(override)

    override.custom_title = payload.custom_title
    override.custom_description = payload.custom_description
    override.custom_price = payload.custom_price
    override.custom_tags = payload.custom_tags
    override.category_mapping = payload.category_mapping
    override.is_approved_for_channel = payload.is_approved_for_channel

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="CHANNEL_OVERRIDE_UPSERTED",
        resource_type="product_channel_override",
        resource_id=f"{product_id}_{channel}",
        metadata_json={"channel": channel, "is_approved": payload.is_approved_for_channel},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(override)
    return ProductChannelOverrideRead.model_validate(override)


# ==========================================
# UNIVERSAL CHANNEL REQUIREMENTS & STOCK SYNC
# ==========================================
class ChannelRequirementsCheckRequest(BaseModel):
    channels: Optional[List[str]] = None
    channel: Optional[str] = None


@router.post("/{product_id}/channel-requirements")
async def check_product_channel_requirements(
    product_id: uuid.UUID,
    payload: ChannelRequirementsCheckRequest,
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Evaluates master product attributes against genuine category requirements for selected channels."""
    from backend.app.services.mapping.channel_mapper import ChannelMapper

    target_channels = payload.channels or ([payload.channel] if payload.channel else ["shopify", "woocommerce", "amazon", "flipkart"])

    res = await db.execute(
        select(Product)
        .options(
            selectinload(Product.variants),
            selectinload(Product.media),
            selectinload(Product.overrides),
        )
        .where(
            Product.id == product_id,
            Product.organization_id == context.organization_id,
        )
    )
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in this organization.")

    res_dict = ChannelMapper.check_all_channel_requirements(
        product=product,
        channels=target_channels,
    )
    return {
        "product_id": str(product_id),
        "channels": res_dict,
        **res_dict,
    }


class StockSyncRequest(BaseModel):
    stock_quantity: int


@router.post("/{product_id}/sync-stock")
async def sync_product_stock_across_channels(
    product_id: uuid.UUID,
    payload: StockSyncRequest,
    context: TenantContext = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Updates master SKU stock and queues synchronization jobs to all active connected channels."""
    from backend.app.services.order_sync_service import OrderSyncService

    res = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.organization_id == context.organization_id,
        )
    )
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in this organization.")

    product.stock_quantity = payload.stock_quantity
    await db.flush()

    jobs_queued = await OrderSyncService.queue_cross_channel_stock_sync(
        db=db,
        organization_id=context.organization_id,
        source_channel="master_manual",
        items_stock=[(product.sku, payload.stock_quantity)],
    )

    await db.commit()
    return {
        "success": True,
        "sku": product.sku,
        "new_stock": payload.stock_quantity,
        "channel_sync_jobs_queued": jobs_queued,
    }


# ==========================================
# UNIFIED PRODUCT VOICE & TEXT INTAKE
# ==========================================
class ProductExtractTextRequest(BaseModel):
    text: str
    category_hint: Optional[str] = None


class ProductVoiceIntakeRequest(BaseModel):
    audio_base64: Optional[str] = None
    mime_type: Optional[str] = "audio/webm"
    transcript: Optional[str] = None
    category_hint: Optional[str] = None


@router.post("/extract-from-text")
async def extract_product_from_text(
    payload: ProductExtractTextRequest,
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer"])),
):
    """Processes unstructured seller product descriptions and generates a structured master draft."""
    from backend.app.services.product_intake_service import ProductIntakeService

    if not payload.text or len(payload.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Please provide product notes to extract.")

    draft = await ProductIntakeService.extract_from_text(
        text=payload.text,
        category_hint=payload.category_hint,
    )
    return draft.model_dump()


@router.post("/voice-intake")
async def extract_product_from_voice(
    payload: ProductVoiceIntakeRequest,
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer"])),
):
    """Extracts structured product specifications from spoken voice recordings or audio streams."""
    import base64
    from backend.app.services.product_intake_service import ProductIntakeService

    if payload.audio_base64:
        try:
            raw_b64 = payload.audio_base64.split(",")[-1]
            audio_bytes = base64.b64decode(raw_b64)
            draft = await ProductIntakeService.extract_from_audio(
                audio_bytes=audio_bytes,
                mime_type=payload.mime_type or "audio/webm",
                category_hint=payload.category_hint,
            )
            return draft.model_dump()
        except Exception as e:
            logger.warning(f"Voice audio decode error: {e}")

    if payload.transcript:
        draft = await ProductIntakeService.extract_from_text(
            text=payload.transcript,
            category_hint=payload.category_hint,
        )
        return draft.model_dump()

    raise HTTPException(status_code=400, detail="Please provide audio recording or transcript.")




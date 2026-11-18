"""Publishing Hub API Router.

Provides channel-specific payload previews, validation reports, job dispatching,
asynchronous execution, attempt history logs, and safe idempotent retries.
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.models.catalogue import Product
from backend.app.models.channel import ChannelConnection, ChannelListing, PublishingAttempt, PublishingBatch, PublishingJob
from backend.app.schemas.publishing import (
    BatchPreviewRequest,
    BatchPreviewResponse,
    ChannelListingRead,
    PublishBatchCreate,
    PublishBatchRead,
    PublishJobCreate,
    PublishJobRead,
    PublishPreviewRequest,
    PublishPreviewResponse,
)
from backend.app.services.publishing_engine import PublishingEngine, PublishingEngineError
from backend.app.services.publishing_orchestrator import (
    ApprovalHashMismatchError,
    PublishingOrchestrator,
)

router = APIRouter()


def _format_job_read(
    job: PublishingJob,
    product: Optional[Product] = None,
    listing: Optional[ChannelListing] = None,
    attempts: Optional[List[PublishingAttempt]] = None,
) -> Dict[str, Any]:
    """Helper to transform PublishingJob model to PublishJobRead schema."""
    conn = job.connection
    channel_type = conn.channel_type if conn else "unknown"
    account_name = conn.account_name if conn else "Unknown Account"

    prod_title = product.title if product else (job.payload_snapshot.get("input", {}).get("title") or "Product")
    prod_sku = product.sku if product else "SKU"

    remote_id = listing.remote_product_id if listing else None
    remote_url = listing.remote_url if listing else None

    resolved_attempts = attempts if attempts is not None else (job.attempts or [])

    if not remote_id and resolved_attempts:
        for att in reversed(resolved_attempts):
            if att.response_payload and isinstance(att.response_payload, dict):
                r_id = att.response_payload.get("id") or att.response_payload.get("submission_id") or att.response_payload.get("listing_id")
                if r_id is not None:
                    remote_id = str(r_id)
                r_url = att.response_payload.get("permalink") or att.response_payload.get("remote_url")
                if r_url:
                    remote_url = str(r_url)
                if remote_id:
                    break

    # Determine error summary if failed
    error_summary = None
    if job.status == "failed" and resolved_attempts:
        last_attempt = sorted(resolved_attempts, key=lambda a: a.attempt_number)[-1]
        error_summary = last_attempt.error_message

    return {
        "id": job.id,
        "organization_id": job.organization_id,
        "product_id": job.product_id,
        "channel_connection_id": job.channel_connection_id,
        "channel_type": channel_type,
        "account_name": account_name,
        "product_title": prod_title,
        "product_sku": prod_sku,
        "idempotency_key": job.idempotency_key,
        "job_type": job.job_type,
        "status": job.status,
        "payload_snapshot": job.payload_snapshot,
        "retry_count": job.retry_count,
        "scheduled_at": job.scheduled_at,
        "completed_at": job.completed_at,
        "created_at": job.created_at,
        "attempts": [
            {
                "id": a.id,
                "attempt_number": a.attempt_number,
                "http_status": a.http_status,
                "error_message": a.error_message,
                "attempted_at": a.attempted_at,
            }
            for a in resolved_attempts
        ],
        "remote_product_id": remote_id,
        "remote_url": remote_url,
        "error_summary": error_summary,
    }


@router.post("/preview", response_model=PublishPreviewResponse)
async def preview_channel_payload(
    payload: PublishPreviewRequest,
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Generates preview of the platform-specific payload and validation results."""
    try:
        preview_data = await PublishingEngine.create_preview(
            session=db,
            organization_id=tenant.organization_id,
            product_id=payload.product_id,
            channel_type=payload.channel_type,
        )
        return preview_data
    except PublishingEngineError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/jobs", response_model=PublishJobRead, status_code=status.HTTP_201_CREATED)
async def create_publishing_job(
    payload: PublishJobCreate,
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Enqueues and executes a publishing job for an authorized sales/marketing channel."""
    try:
        job = await PublishingEngine.enqueue_job(
            session=db,
            organization_id=tenant.organization_id,
            product_id=payload.product_id,
            channel_connection_id=payload.channel_connection_id,
            job_type=payload.job_type,
            idempotency_key=payload.idempotency_key,
            scheduled_at=payload.scheduled_at,
        )

        # If not scheduled in the future, execute immediately
        if job.status == "queued":
            job = await PublishingEngine.execute_job(session=db, job_id=job.id)

        # Fetch product, listing & attempts to format response
        prod = await db.get(Product, job.product_id)
        stmt_listing = select(ChannelListing).where(
            ChannelListing.channel_connection_id == job.channel_connection_id,
            ChannelListing.product_id == job.product_id,
        )
        res_listing = await db.execute(stmt_listing)
        listing = res_listing.scalar_one_or_none()

        stmt_attempts = (
            select(PublishingAttempt)
            .where(PublishingAttempt.job_id == job.id)
            .order_by(PublishingAttempt.attempt_number)
        )
        res_attempts = await db.execute(stmt_attempts)
        attempts = list(res_attempts.scalars().all())

        return _format_job_read(job, prod, listing, attempts)

    except PublishingEngineError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/jobs", response_model=List[PublishJobRead])
async def list_publishing_jobs(
    channel_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists publishing jobs for this organization with attempt logs."""
    stmt = (
        select(PublishingJob)
        .where(PublishingJob.organization_id == tenant.organization_id)
        .options(
            selectinload(PublishingJob.connection),
            selectinload(PublishingJob.attempts),
        )
        .order_by(desc(PublishingJob.created_at))
    )

    if status_filter:
        stmt = stmt.where(PublishingJob.status == status_filter)

    result = await db.execute(stmt)
    jobs = result.scalars().all()

    # Preload products and listings
    prod_ids = [j.product_id for j in jobs]
    prods: Dict[uuid.UUID, Product] = {}
    if prod_ids:
        p_stmt = select(Product).where(Product.id.in_(prod_ids))
        p_res = await db.execute(p_stmt)
        prods = {p.id: p for p in p_res.scalars().all()}

    listings_stmt = select(ChannelListing).where(ChannelListing.product_id.in_(prod_ids)) if prod_ids else None
    listings_map: Dict[str, ChannelListing] = {}
    if listings_stmt is not None:
        l_res = await db.execute(listings_stmt)
        for l in l_res.scalars().all():
            listings_map[f"{l.channel_connection_id}_{l.product_id}"] = l

    formatted_jobs: List[Dict[str, Any]] = []
    for j in jobs:
        if channel_type and j.connection and j.connection.channel_type != channel_type:
            continue
        p = prods.get(j.product_id)
        l = listings_map.get(f"{j.channel_connection_id}_{j.product_id}")
        formatted_jobs.append(_format_job_read(j, p, l))

    return formatted_jobs


@router.get("/jobs/{job_id}", response_model=PublishJobRead)
async def get_publishing_job(
    job_id: uuid.UUID,
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Fetches single publishing job with detailed attempt history."""
    stmt = (
        select(PublishingJob)
        .where(PublishingJob.id == job_id, PublishingJob.organization_id == tenant.organization_id)
        .options(
            selectinload(PublishingJob.connection),
            selectinload(PublishingJob.attempts),
        )
    )
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publishing job not found.")

    prod = await db.get(Product, job.product_id)
    stmt_listing = select(ChannelListing).where(
        ChannelListing.channel_connection_id == job.channel_connection_id,
        ChannelListing.product_id == job.product_id,
    )
    res_listing = await db.execute(stmt_listing)
    listing = res_listing.scalar_one_or_none()

    return _format_job_read(job, prod, listing)


@router.post("/jobs/{job_id}/retry", response_model=PublishJobRead)
async def retry_publishing_job(
    job_id: uuid.UUID,
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Safely and idempotently retries a failed publishing job."""
    stmt = (
        select(PublishingJob)
        .where(PublishingJob.id == job_id, PublishingJob.organization_id == tenant.organization_id)
        .options(
            selectinload(PublishingJob.connection),
            selectinload(PublishingJob.attempts),
        )
    )
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publishing job not found.")

    if job.status == "published":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job has already succeeded.")

    updated_job = await PublishingEngine.execute_job(session=db, job_id=job.id)

    prod = await db.get(Product, updated_job.product_id)
    stmt_listing = select(ChannelListing).where(
        ChannelListing.channel_connection_id == updated_job.channel_connection_id,
        ChannelListing.product_id == updated_job.product_id,
    )
    res_listing = await db.execute(stmt_listing)
    listing = res_listing.scalar_one_or_none()

    stmt_attempts = (
        select(PublishingAttempt)
        .where(PublishingAttempt.job_id == updated_job.id)
        .order_by(PublishingAttempt.attempt_number)
    )
    res_attempts = await db.execute(stmt_attempts)
    attempts = list(res_attempts.scalars().all())

    return _format_job_read(updated_job, prod, listing, attempts)


async def _format_batch_read(batch: PublishingBatch, db: AsyncSession) -> Dict[str, Any]:
    """Helper to transform PublishingBatch model to PublishBatchRead schema with linked listings."""
    prod_ids = [j.product_id for j in (batch.jobs or [])]
    conn_ids = [j.channel_connection_id for j in (batch.jobs or [])]
    listings_map: Dict[str, ChannelListing] = {}
    if prod_ids and conn_ids:
        l_stmt = select(ChannelListing).where(
            ChannelListing.product_id.in_(prod_ids),
            ChannelListing.channel_connection_id.in_(conn_ids),
        )
        l_res = await db.execute(l_stmt)
        for l in l_res.scalars().all():
            listings_map[f"{l.channel_connection_id}_{l.product_id}"] = l

    jobs_formatted = []
    for j in batch.jobs or []:
        l = listings_map.get(f"{j.channel_connection_id}_{j.product_id}")
        jobs_formatted.append(_format_job_read(j, listing=l))
    return {
        "id": batch.id,
        "organization_id": batch.organization_id,
        "product_id": batch.product_id,
        "status": batch.status,
        "channels": batch.channels or [],
        "approved_by_user_id": batch.approved_by_user_id,
        "approved_at": batch.approved_at,
        "approval_hash": batch.approval_hash,
        "approval_snapshot": batch.approval_snapshot or {},
        "notes": batch.notes,
        "created_at": batch.created_at,
        "jobs": jobs_formatted,
    }


@router.post("/batch-preview", response_model=BatchPreviewResponse)
async def preview_batch_channels(
    payload: BatchPreviewRequest,
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Generates pre-flight validation previews for multiple selected channels with approval hash."""
    try:
        return await PublishingOrchestrator.prepare_batch_preview(
            session=db,
            organization_id=tenant.organization_id,
            product_id=payload.product_id,
            channel_types=payload.channel_types,
        )
    except PublishingEngineError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/batches", response_model=PublishBatchRead, status_code=status.HTTP_201_CREATED)
async def dispatch_publishing_batch(
    payload: PublishBatchCreate,
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Enforces immutable seller approval verification and dispatches a multi-channel publishing batch."""
    try:
        batch = await PublishingOrchestrator.dispatch_batch(
            session=db,
            organization_id=tenant.organization_id,
            user_id=tenant.user.id,
            product_id=payload.product_id,
            channel_connection_ids=payload.channel_connection_ids,
            approval_hash=payload.approval_hash,
            notes=payload.notes,
        )
        return await _format_batch_read(batch, db)
    except ApprovalHashMismatchError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PublishingEngineError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/batches", response_model=List[PublishBatchRead])
async def list_publishing_batches(
    status_filter: Optional[str] = Query(None, alias="status"),
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists omnichannel publishing batches for this organization with per-channel job states."""
    stmt = (
        select(PublishingBatch)
        .where(PublishingBatch.organization_id == tenant.organization_id)
        .options(
            selectinload(PublishingBatch.jobs).selectinload(PublishingJob.connection),
            selectinload(PublishingBatch.jobs).selectinload(PublishingJob.attempts),
        )
        .order_by(desc(PublishingBatch.created_at))
    )
    if status_filter:
        stmt = stmt.where(PublishingBatch.status == status_filter)

    res = await db.execute(stmt)
    batches = res.scalars().all()
    return [await _format_batch_read(b, db) for b in batches]


@router.get("/batches/{batch_id}", response_model=PublishBatchRead)
async def get_publishing_batch(
    batch_id: uuid.UUID,
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Fetches a single publishing batch with detailed per-channel execution records."""
    stmt = (
        select(PublishingBatch)
        .where(PublishingBatch.id == batch_id, PublishingBatch.organization_id == tenant.organization_id)
        .options(
            selectinload(PublishingBatch.jobs).selectinload(PublishingJob.connection),
            selectinload(PublishingBatch.jobs).selectinload(PublishingJob.attempts),
        )
    )
    res = await db.execute(stmt)
    batch = res.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publishing batch not found.")

    return await _format_batch_read(batch, db)


@router.post("/batches/{batch_id}/retry", response_model=PublishBatchRead)
async def retry_publishing_batch(
    batch_id: uuid.UUID,
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Safely and idempotently retries failed jobs in an existing publishing batch."""
    try:
        refreshed_batch = await PublishingOrchestrator.retry_batch_failed_jobs(
            session=db,
            organization_id=tenant.organization_id,
            batch_id=batch_id,
        )
        return await _format_batch_read(refreshed_batch, db)
    except PublishingEngineError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/listings", response_model=List[ChannelListingRead])
async def list_channel_listings(
    channel_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    tenant: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists external channel listings across all connected storefronts and marketplaces."""
    stmt = (
        select(ChannelListing)
        .join(ChannelConnection, ChannelListing.channel_connection_id == ChannelConnection.id)
        .join(Product, ChannelListing.product_id == Product.id)
        .where(ChannelConnection.organization_id == tenant.organization_id)
        .options(
            selectinload(ChannelListing.connection),
        )
        .order_by(desc(ChannelListing.last_published_at))
    )

    if channel_type:
        stmt = stmt.where(ChannelConnection.channel_type == channel_type)
    if status_filter:
        stmt = stmt.where(ChannelListing.remote_status == status_filter)

    res = await db.execute(stmt)
    listings = res.scalars().all()

    prod_ids = [l.product_id for l in listings]
    prods: Dict[uuid.UUID, Product] = {}
    if prod_ids:
        p_res = await db.execute(select(Product).where(Product.id.in_(prod_ids)))
        prods = {p.id: p for p in p_res.scalars().all()}

    items = []
    for l in listings:
        p = prods.get(l.product_id)
        items.append({
            "id": l.id,
            "product_id": l.product_id,
            "product_title": l.channel_title or (p.title if p else "Product"),
            "product_sku": l.external_sku or (p.sku if p else "SKU"),
            "channel_connection_id": l.channel_connection_id,
            "channel_type": l.connection.channel_type if l.connection else "unknown",
            "account_name": l.connection.account_name if l.connection else "Unknown",
            "remote_product_id": l.remote_product_id,
            "remote_url": l.remote_url,
            "remote_status": l.remote_status,
            "last_published_at": l.last_published_at,
            "price": float(l.channel_price) if l.channel_price is not None else (float(p.base_price) if p else 0.0),
            "stock_quantity": int(p.stock_quantity or 0) if p else 0,
            "external_sku": l.external_sku,
            "channel_title": l.channel_title,
            "channel_price": l.channel_price,
            "last_error": l.last_error,
        })
    return items

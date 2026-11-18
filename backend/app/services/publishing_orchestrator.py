"""Publishing Orchestrator.

Orchestrates multi-channel publishing batches with immutable approval snapshot verification,
independent per-channel job dispatch, idempotency, partial success handling, and audit logging.
"""

import datetime
import hashlib
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.audit import AuditLog
from backend.app.models.catalogue import Product, ProductChannelOverride
from backend.app.models.channel import ChannelConnection, ChannelListing, PublishingBatch, PublishingJob
from backend.app.services.publishing_engine import PublishingEngine, PublishingEngineError

logger = logging.getLogger(__name__)


class ApprovalHashMismatchError(PublishingEngineError):
    """Raised when product specifications changed after approval preview was generated."""
    pass


class PublishingOrchestrator:
    """Coordinates omnichannel batch listings, seller approvals, and status reconciliation."""

    @staticmethod
    def compute_product_hash(product: Product, overrides: Optional[List[ProductChannelOverride]] = None) -> str:
        """Computes deterministic SHA-256 hash of product catalogue specifications and channel overrides."""
        norm_data = {
            "id": str(product.id),
            "title": product.title or "",
            "sku": product.sku or "",
            "base_price": float(product.base_price or 0.0),
            "compare_at_price": float(product.compare_at_price or 0.0) if product.compare_at_price else None,
            "category": product.category or "",
            "short_description": product.short_description or "",
            "long_description": product.long_description or "",
            "weight": float(product.weight or 0.0),
            "dimensions": product.dimensions or {},
            "category_attributes": product.category_attributes or {},
            "packaging_specs": product.packaging_specs or {},
            "shipping_specs": product.shipping_specs or {},
            "variants": [
                {
                    "sku": v.sku,
                    "title": v.title,
                    "price": float(v.price),
                    "options": v.options,
                }
                for v in sorted(product.variants or [], key=lambda x: x.sku or "")
            ],
            "overrides": [
                {
                    "channel": o.channel_type,
                    "custom_title": o.custom_title,
                    "custom_price": float(o.custom_price) if o.custom_price else None,
                    "category_mapping": o.category_mapping,
                    "is_approved": o.is_approved_for_channel,
                }
                for o in sorted(overrides or [], key=lambda x: x.channel_type)
            ],
        }
        encoded = json.dumps(norm_data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    async def prepare_batch_preview(
        cls,
        session: AsyncSession,
        organization_id: uuid.UUID,
        product_id: uuid.UUID,
        channel_types: List[str],
    ) -> Dict[str, Any]:
        """Generates unified multi-channel preview, validation reports, and cryptographic approval hash."""
        stmt = (
            select(Product)
            .where(Product.id == product_id, Product.organization_id == organization_id)
            .options(
                selectinload(Product.variants),
                selectinload(Product.media),
                selectinload(Product.overrides),
            )
        )
        res = await session.execute(stmt)
        product = res.scalar_one_or_none()
        if not product:
            raise PublishingEngineError(f"Product {product_id} not found in this organization.")

        channel_previews: Dict[str, Any] = {}
        all_valid = True

        for ch in channel_types:
            try:
                prev = await PublishingEngine.create_preview(
                    session=session,
                    organization_id=organization_id,
                    product_id=product_id,
                    channel_type=ch,
                )
                channel_previews[ch] = prev
                if not prev.get("validation_passed", False):
                    all_valid = False
            except Exception as e:
                channel_previews[ch] = {
                    "channel_type": ch,
                    "validation_passed": False,
                    "validation_errors": [str(e)],
                    "validation_warnings": [],
                    "payload_preview": {},
                }
                all_valid = False

        approval_hash = cls.compute_product_hash(product, product.overrides)

        return {
            "product_id": str(product.id),
            "product_title": product.title,
            "product_sku": product.sku,
            "channels": channel_types,
            "overall_valid": all_valid,
            "approval_hash": approval_hash,
            "channel_previews": channel_previews,
        }

    @classmethod
    async def dispatch_batch(
        cls,
        session: AsyncSession,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        channel_connection_ids: List[uuid.UUID],
        approval_hash: str,
        notes: Optional[str] = None,
    ) -> PublishingBatch:
        """Dispatches an immutable certified batch to all selected channel connections."""
        # 1. Fetch product with relationships
        stmt = (
            select(Product)
            .where(Product.id == product_id, Product.organization_id == organization_id)
            .options(
                selectinload(Product.variants),
                selectinload(Product.media),
                selectinload(Product.overrides),
            )
        )
        res = await session.execute(stmt)
        product = res.scalar_one_or_none()
        if not product:
            raise PublishingEngineError(f"Product {product_id} not found in this organization.")

        # 2. Immutable hash verification
        current_hash = cls.compute_product_hash(product, product.overrides)
        if current_hash != approval_hash:
            raise ApprovalHashMismatchError(
                "Product specifications or overrides were modified after the preview was approved. "
                "Please review the updated product specifications and certify a fresh approval."
            )

        # 3. Fetch connections
        conn_stmt = select(ChannelConnection).where(
            ChannelConnection.id.in_(channel_connection_ids),
            ChannelConnection.organization_id == organization_id,
        )
        conn_res = await session.execute(conn_stmt)
        connections = conn_res.scalars().all()
        if not connections:
            raise PublishingEngineError("No valid channel connections found for this batch.")

        channel_types = [c.channel_type for c in connections]

        # 4. Construct approval snapshot
        approval_snapshot = {
            "approved_by_user_id": str(user_id),
            "approved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "approval_hash": approval_hash,
            "product": {
                "id": str(product.id),
                "title": product.title,
                "sku": product.sku,
                "base_price": float(product.base_price),
                "category": product.category,
            },
            "channels": channel_types,
        }

        # 5. Create PublishingBatch record
        batch = PublishingBatch(
            organization_id=organization_id,
            product_id=product_id,
            status="processing",
            channels=channel_types,
            approved_by_user_id=user_id,
            approval_hash=approval_hash,
            approval_snapshot=approval_snapshot,
            notes=notes,
        )
        session.add(batch)
        await session.flush()

        # 6. Dispatch per-channel jobs independently
        jobs: List[PublishingJob] = []
        for conn in connections:
            idempotency_key = f"batch_{batch.id}_{conn.channel_type}_{product_id}"
            try:
                job = await PublishingEngine.enqueue_job(
                    session=session,
                    organization_id=organization_id,
                    product_id=product_id,
                    channel_connection_id=conn.id,
                    job_type="create_listing",
                    idempotency_key=idempotency_key,
                    batch_id=batch.id,
                )
                # Execute job immediately
                if job.status == "queued":
                    job = await PublishingEngine.execute_job(session=session, job_id=job.id)
                jobs.append(job)
            except Exception as e:
                logger.error(f"Failed to dispatch job for {conn.channel_type}: {e}")

        # 7. Reconcile final batch status
        published_count = sum(1 for j in jobs if j.status == "published")
        failed_count = sum(1 for j in jobs if j.status == "failed")

        if published_count == len(connections):
            batch.status = "completed"
            batch.notes = f"All {published_count} channel listings published successfully."
        elif published_count > 0:
            batch.status = "partially_completed"
            batch.notes = f"{published_count} of {len(connections)} channels published; {failed_count} failed."
        else:
            batch.status = "failed"
            batch.notes = f"All {len(connections)} channel publishing jobs failed."

        # 8. Record audit log
        audit = AuditLog(
            organization_id=organization_id,
            actor_user_id=user_id,
            action="PUBLISHING_BATCH_DISPATCHED",
            resource_type="publishing_batch",
            resource_id=str(batch.id),
            metadata_json={
                "batch_id": str(batch.id),
                "product_id": str(product_id),
                "channels": channel_types,
                "status": batch.status,
                "published_count": published_count,
                "failed_count": failed_count,
            },
        )
        session.add(audit)
        await session.commit()

        # Reload with relationships using populate_existing
        reload_stmt = (
            select(PublishingBatch)
            .where(PublishingBatch.id == batch.id)
            .execution_options(populate_existing=True)
            .options(
                selectinload(PublishingBatch.jobs).selectinload(PublishingJob.connection),
                selectinload(PublishingBatch.jobs).selectinload(PublishingJob.attempts),
            )
        )
        reload_res = await session.execute(reload_stmt)
        return reload_res.scalar_one()

    @classmethod
    async def retry_batch_failed_jobs(
        cls,
        session: AsyncSession,
        organization_id: uuid.UUID,
        batch_id: uuid.UUID,
    ) -> PublishingBatch:
        """Safely and idempotently retries failed jobs in an existing batch."""
        stmt = (
            select(PublishingBatch)
            .where(PublishingBatch.id == batch_id, PublishingBatch.organization_id == organization_id)
            .options(
                selectinload(PublishingBatch.jobs).selectinload(PublishingJob.connection),
                selectinload(PublishingBatch.jobs).selectinload(PublishingJob.attempts),
            )
        )
        res = await session.execute(stmt)
        batch = res.scalar_one_or_none()
        if not batch:
            raise PublishingEngineError(f"Publishing batch {batch_id} not found.")

        retried_jobs = []
        for job in batch.jobs:
            if job.status == "failed":
                updated = await PublishingEngine.execute_job(session=session, job_id=job.id)
                retried_jobs.append(updated)

        # Re-evaluate batch status
        reload_res = await session.execute(stmt.execution_options(populate_existing=True))
        refreshed_batch = reload_res.scalar_one()

        published_count = sum(1 for j in refreshed_batch.jobs if j.status == "published")
        total_jobs = len(refreshed_batch.jobs)

        if published_count == total_jobs:
            refreshed_batch.status = "completed"
        elif published_count > 0:
            refreshed_batch.status = "partially_completed"
        else:
            refreshed_batch.status = "failed"

        await session.commit()
        return refreshed_batch

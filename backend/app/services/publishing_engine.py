"""Publishing Queue and Job Execution Engine.

Handles asynchronous job dispatching, channel mapping snapshot generation,
idempotent retries, external API execution, and audit logging into publishing_attempts.
"""

import datetime
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.security import decrypt_token
from backend.app.models.catalogue import Product, ProductChannelOverride
from backend.app.models.channel import ChannelConnection, ChannelListing, PublishingAttempt, PublishingJob
from backend.app.services.amazon_service import AmazonSPAPIError, AmazonService
from backend.app.services.flipkart_service import FlipkartAPIError, FlipkartService
from backend.app.services.instagram_service import InstagramError, InstagramService
from backend.app.services.mapping.channel_mapper import ChannelMapper
from backend.app.services.shopify_service import ShopifyError, ShopifyService
from backend.app.services.woocommerce_service import WooCommerceError, WooCommerceService

logger = logging.getLogger(__name__)


class PublishingEngineError(Exception):
    """Raised on publishing workflow errors."""
    pass


class PublishingEngine:
    """Orchestrates omnichannel publishing jobs with full audit logging and idempotency."""

    @classmethod
    async def create_preview(
        cls,
        session: AsyncSession,
        organization_id: uuid.UUID,
        product_id: uuid.UUID,
        channel_type: str,
    ) -> Dict[str, Any]:
        """Generates a channel-specific payload preview and validation report."""
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

        # Find override for channel
        override = next((o for o in (product.overrides or []) if o.channel_type == channel_type), None)

        if channel_type == "shopify":
            is_valid, errors, warnings = ChannelMapper.validate_for_shopify(product, override)
            payload = ChannelMapper.map_to_shopify_graphql(product, override)
        elif channel_type == "woocommerce":
            is_valid, errors, warnings = ChannelMapper.validate_for_woocommerce(product, override)
            payload = ChannelMapper.map_to_woocommerce(product, override)
        elif channel_type == "amazon":
            is_valid, errors, warnings = ChannelMapper.validate_for_amazon(product, override)
            payload = ChannelMapper.map_to_amazon_sp_api(product, override)
        elif channel_type == "flipkart":
            is_valid, errors, warnings = ChannelMapper.validate_for_flipkart(product, override)
            payload = ChannelMapper.map_to_flipkart(product, override)
        elif channel_type == "instagram":
            is_valid, errors, warnings = ChannelMapper.validate_for_instagram(product, override)
            payload = ChannelMapper.map_to_instagram_post(product, override)
        else:
            raise PublishingEngineError(f"Unsupported channel type for preview: {channel_type}")

        return {
            "product_id": product.id,
            "channel_type": channel_type,
            "payload_preview": payload,
            "validation_passed": is_valid,
            "validation_warnings": warnings,
            "validation_errors": errors,
            "master_source": {
                "title": product.title,
                "sku": product.sku,
                "base_price": float(product.base_price),
                "media_count": len(product.media or []),
                "variant_count": len(product.variants or []),
            },
            "overrides_applied": override is not None,
        }

    @classmethod
    async def enqueue_job(
        cls,
        session: AsyncSession,
        organization_id: uuid.UUID,
        product_id: uuid.UUID,
        channel_connection_id: uuid.UUID,
        job_type: str = "create_listing",
        idempotency_key: Optional[str] = None,
        scheduled_at: Optional[datetime.datetime] = None,
        batch_id: Optional[uuid.UUID] = None,
    ) -> PublishingJob:
        """Enqueues a publishing job with an idempotency key and snapshot."""
        # 1. Fetch channel connection
        stmt_conn = select(ChannelConnection).where(
            ChannelConnection.id == channel_connection_id,
            ChannelConnection.organization_id == organization_id,
        )
        res_conn = await session.execute(stmt_conn)
        connection = res_conn.scalar_one_or_none()
        if not connection:
            raise PublishingEngineError("Channel connection not found or does not belong to this organization.")

        if connection.status != "active":
            raise PublishingEngineError(f"Channel connection is {connection.status}. Reconnection is required.")

        # 2. Idempotency check
        if not idempotency_key:
            idempotency_key = f"pub_{connection.channel_type}_{product_id}_{uuid.uuid4().hex[:12]}"

        stmt_existing = (
            select(PublishingJob)
            .where(PublishingJob.idempotency_key == idempotency_key)
            .options(
                selectinload(PublishingJob.connection),
                selectinload(PublishingJob.attempts),
            )
        )
        res_existing = await session.execute(stmt_existing)
        existing_job = res_existing.scalar_one_or_none()
        if existing_job:
            logger.info(f"Idempotent job return for key: {idempotency_key}")
            return existing_job

        # 3. Fetch product with relationships
        stmt_prod = (
            select(Product)
            .where(Product.id == product_id, Product.organization_id == organization_id)
            .options(
                selectinload(Product.variants),
                selectinload(Product.media),
                selectinload(Product.overrides),
            )
        )
        res_prod = await session.execute(stmt_prod)
        product = res_prod.scalar_one_or_none()
        if not product:
            raise PublishingEngineError("Product not found.")

        # 4. Generate payload snapshot
        override = next((o for o in (product.overrides or []) if o.channel_type == connection.channel_type), None)
        if connection.channel_type == "shopify":
            is_valid, errors, _ = ChannelMapper.validate_for_shopify(product, override)
            if not is_valid:
                raise PublishingEngineError(f"Product cannot be published to Shopify: {'; '.join(errors)}")
            payload_snapshot = ChannelMapper.map_to_shopify_graphql(product, override)
        elif connection.channel_type == "woocommerce":
            is_valid, errors, _ = ChannelMapper.validate_for_woocommerce(product, override)
            if not is_valid:
                raise PublishingEngineError(f"Product cannot be published to WooCommerce: {'; '.join(errors)}")
            payload_snapshot = ChannelMapper.map_to_woocommerce(product, override)
        elif connection.channel_type == "amazon":
            is_valid, errors, _ = ChannelMapper.validate_for_amazon(product, override)
            if not is_valid:
                raise PublishingEngineError(f"Product cannot be published to Amazon India: {'; '.join(errors)}")
            payload_snapshot = ChannelMapper.map_to_amazon_sp_api(product, override)
        elif connection.channel_type == "flipkart":
            is_valid, errors, _ = ChannelMapper.validate_for_flipkart(product, override)
            if not is_valid:
                raise PublishingEngineError(f"Product cannot be published to Flipkart: {'; '.join(errors)}")
            payload_snapshot = ChannelMapper.map_to_flipkart(product, override)
        elif connection.channel_type == "instagram":
            is_valid, errors, _ = ChannelMapper.validate_for_instagram(product, override)
            if not is_valid:
                raise PublishingEngineError(f"Product cannot be published to Instagram: {'; '.join(errors)}")
            payload_snapshot = ChannelMapper.map_to_instagram_post(product, override)
        else:
            raise PublishingEngineError(f"Unsupported channel type: {connection.channel_type}")

        initial_status = "scheduled" if (scheduled_at and scheduled_at > datetime.datetime.now(datetime.timezone.utc)) else "queued"

        job = PublishingJob(
            organization_id=organization_id,
            product_id=product.id,
            channel_connection_id=connection.id,
            batch_id=batch_id,
            idempotency_key=idempotency_key,
            job_type=job_type,
            status=initial_status,
            payload_snapshot=payload_snapshot,
            retry_count=0,
            scheduled_at=scheduled_at,
        )
        session.add(job)
        await session.commit()
        stmt_reload = (
            select(PublishingJob)
            .where(PublishingJob.id == job.id)
            .options(
                selectinload(PublishingJob.connection),
                selectinload(PublishingJob.attempts),
            )
        )
        res_reload = await session.execute(stmt_reload)
        return res_reload.scalar_one()

    @classmethod
    async def execute_job(
        cls,
        session: AsyncSession,
        job_id: uuid.UUID,
        client: Optional[httpx.AsyncClient] = None,
    ) -> PublishingJob:
        """Executes a queued publishing job, contacting the remote channel API."""
        stmt = (
            select(PublishingJob)
            .where(PublishingJob.id == job_id)
            .options(
                selectinload(PublishingJob.connection),
                selectinload(PublishingJob.attempts),
            )
        )
        res = await session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise PublishingEngineError(f"Publishing job {job_id} not found.")

        connection = job.connection
        if not connection:
            raise PublishingEngineError("Connection associated with job no longer exists.")

        job.status = "processing"
        await session.commit()

        attempt_num = len(job.attempts or []) + 1
        access_token = decrypt_token(connection.encrypted_access_token)
        p_res = await session.get(Product, job.product_id)

        try:
            if connection.channel_type == "shopify":
                result = await ShopifyService.create_product_listing(
                    shop_domain=connection.account_identifier,
                    access_token=access_token,
                    payload=job.payload_snapshot,
                    client=client,
                )
            elif connection.channel_type == "instagram":
                result = await InstagramService.publish_organic_post(
                    ig_user_id=connection.account_identifier,
                    access_token=access_token,
                    payload=job.payload_snapshot,
                    client=client,
                )
            elif connection.channel_type == "woocommerce":
                consumer_key = None
                consumer_secret = None
                if access_token:
                    if ":" in access_token:
                        consumer_key, consumer_secret = access_token.split(":", 1)
                    elif "{" in access_token:
                        try:
                            token_data = json.loads(access_token)
                            consumer_key = token_data.get("consumer_key")
                            consumer_secret = token_data.get("consumer_secret")
                        except Exception:
                            pass
                wc_svc = WooCommerceService(
                    store_url=connection.account_identifier,
                    consumer_key=consumer_key,
                    consumer_secret=consumer_secret,
                )
                wc_res = await wc_svc.create_product(job.payload_snapshot, client=client)
                result = {
                    "remote_product_id": str(wc_res.get("id")),
                    "remote_url": wc_res.get("permalink"),
                    "raw_response": wc_res,
                }
            elif connection.channel_type == "amazon":
                client_id = None
                client_secret = None
                refresh_token = None
                seller_id = connection.account_identifier
                if access_token:
                    try:
                        token_data = json.loads(access_token)
                        client_id = token_data.get("client_id")
                        client_secret = token_data.get("client_secret")
                        refresh_token = token_data.get("refresh_token")
                        seller_id = token_data.get("seller_id") or seller_id
                    except Exception:
                        refresh_token = access_token
                amz_svc = AmazonService(
                    client_id=client_id,
                    client_secret=client_secret,
                    refresh_token=refresh_token,
                    seller_id=seller_id,
                )
                sku = p_res.sku if p_res else "AMZ_SKU"
                amz_res = await amz_svc.submit_listing_item(
                    sku=sku,
                    product_type=p_res.category if p_res else "PRODUCT",
                    attributes=job.payload_snapshot,
                    client=client,
                )
                result = {
                    "remote_product_id": amz_res.get("submission_id") or amz_res.get("sku") or sku,
                    "remote_url": f"https://www.amazon.in/dp/{sku}",
                    "raw_response": amz_res,
                }
            elif connection.channel_type == "flipkart":
                app_id = None
                app_secret = None
                if access_token:
                    if ":" in access_token:
                        app_id, app_secret = access_token.split(":", 1)
                    elif "{" in access_token:
                        try:
                            token_data = json.loads(access_token)
                            app_id = token_data.get("app_id")
                            app_secret = token_data.get("app_secret")
                        except Exception:
                            pass
                flp_svc = FlipkartService(app_id=app_id, app_secret=app_secret)
                sku = p_res.sku if p_res else "FK_SKU"
                flp_res = await flp_svc.create_or_update_listing(
                    sku=sku,
                    listing_payload=job.payload_snapshot,
                    client=client,
                )
                result = {
                    "remote_product_id": flp_res.get("listing_id") or flp_res.get("sku") or sku,
                    "remote_url": f"https://www.flipkart.com/item/{sku}",
                    "raw_response": flp_res,
                }
            else:
                raise PublishingEngineError(f"Unknown channel type {connection.channel_type}")

            # Record success attempt
            attempt = PublishingAttempt(
                job_id=job.id,
                attempt_number=attempt_num,
                http_status=200,
                response_payload=result.get("raw_response"),
                error_message=None,
            )
            session.add(attempt)

            # Update job state
            job.status = "published"
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)

            # Extract title & price for listing record
            channel_title = None
            channel_price = None
            if isinstance(job.payload_snapshot, dict):
                channel_title = (
                    job.payload_snapshot.get("title")
                    or job.payload_snapshot.get("name")
                    or (job.payload_snapshot.get("item_name") if isinstance(job.payload_snapshot.get("item_name"), str) else None)
                )
                channel_price = (
                    job.payload_snapshot.get("price")
                    or job.payload_snapshot.get("regular_price")
                    or (job.payload_snapshot.get("price", {}).get("selling_price") if isinstance(job.payload_snapshot.get("price"), dict) else None)
                )
            if not channel_title and p_res:
                channel_title = p_res.title
            if channel_price is None and p_res:
                channel_price = float(p_res.base_price)
            try:
                channel_price = float(channel_price) if channel_price is not None else None
            except (ValueError, TypeError):
                channel_price = None

            # Upsert channel listing record
            stmt_listing = select(ChannelListing).where(
                ChannelListing.channel_connection_id == connection.id,
                ChannelListing.product_id == job.product_id,
            )
            res_listing = await session.execute(stmt_listing)
            listing = res_listing.scalar_one_or_none()

            if listing:
                listing.organization_id = job.organization_id
                listing.remote_product_id = result["remote_product_id"]
                listing.remote_url = result["remote_url"]
                listing.remote_status = "published"
                listing.external_sku = p_res.sku if p_res else None
                listing.channel_title = channel_title
                listing.channel_price = channel_price
                listing.channel_attributes = job.payload_snapshot
                listing.last_error = None
                listing.last_published_at = datetime.datetime.now(datetime.timezone.utc)
            else:
                listing = ChannelListing(
                    organization_id=job.organization_id,
                    product_id=job.product_id,
                    channel_connection_id=connection.id,
                    remote_product_id=result["remote_product_id"],
                    remote_url=result["remote_url"],
                    remote_status="published",
                    external_sku=p_res.sku if p_res else None,
                    channel_title=channel_title,
                    channel_price=channel_price,
                    channel_attributes=job.payload_snapshot,
                    last_published_at=datetime.datetime.now(datetime.timezone.utc),
                )
                session.add(listing)

            # Update connection sync time
            connection.last_synced_at = datetime.datetime.now(datetime.timezone.utc)
            await session.commit()
            
            stmt_reload = (
                select(PublishingJob)
                .where(PublishingJob.id == job.id)
                .options(
                    selectinload(PublishingJob.connection),
                    selectinload(PublishingJob.attempts),
                )
            )
            res_reload = await session.execute(stmt_reload)
            return res_reload.scalar_one()

        except (ShopifyError, InstagramError, WooCommerceError, AmazonSPAPIError, FlipkartAPIError, Exception) as exc:
            logger.error(f"Error publishing job {job.id}: {exc}")
            error_message = str(exc)
            http_status = getattr(exc, "http_status", 500)

            attempt = PublishingAttempt(
                job_id=job.id,
                attempt_number=attempt_num,
                http_status=http_status,
                response_payload=None,
                error_message=error_message,
            )
            session.add(attempt)

            job.retry_count += 1
            job.status = "failed"
            await session.commit()
            
            stmt_reload = (
                select(PublishingJob)
                .where(PublishingJob.id == job.id)
                .options(
                    selectinload(PublishingJob.connection),
                    selectinload(PublishingJob.attempts),
                )
            )
            res_reload = await session.execute(stmt_reload)
            return res_reload.scalar_one()


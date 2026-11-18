"""Central Order, Stock, and Inventory Synchronisation Engine.

Orchestrates multi-channel order ingestion, SKU resolution, concurrency-safe inventory reservation,
auditable ledger recording, order lifecycle transitions (fulfillment, cancellation, refunds),
and bidirectional stock propagation across all connected selling platforms.
"""

import datetime
import logging
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.audit import AuditLog
from backend.app.models.catalogue import Product, ProductVariant
from backend.app.models.channel import ChannelConnection, PublishingJob
from backend.app.models.order import ChannelOrder, ChannelOrderItem
from backend.app.services.inventory_service import InventoryService
from backend.app.services.reservation_policy import ReservationPolicy
from backend.app.services.shopify_service import ShopifyService
from backend.app.services.woocommerce_service import WooCommerceService
from backend.app.services.amazon_service import AmazonService
from backend.app.services.flipkart_service import FlipkartService

logger = logging.getLogger(__name__)


class OrderSyncService:
    """Service for managing multi-channel orders and stock synchronization."""

    @staticmethod
    async def ingest_order(
        db: AsyncSession,
        organization_id: uuid.UUID,
        channel_type: str,
        remote_order_id: str,
        order_number: str,
        total_amount: float,
        currency: str,
        items_data: List[Dict[str, Any]],
        channel_connection_id: Optional[uuid.UUID] = None,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        financial_status: str = "paid",
        fulfillment_status: str = "unfulfilled",
        order_lifecycle_status: Optional[str] = None,
        subtotal: float = 0.0,
        discount_amount: float = 0.0,
        shipping_amount: float = 0.0,
        tax_amount: float = 0.0,
        shipping_address: Optional[Dict[str, Any]] = None,
        billing_address: Optional[Dict[str, Any]] = None,
        order_date: Optional[datetime.datetime] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ChannelOrder, bool]:
        """Ingests a sales order with strict deduplication, SKU mapping, and inventory reservation.
        
        Returns:
            (order, is_new_order)
        """
        # 1. Idempotency check: prevent duplicate ingestion
        stmt = select(ChannelOrder).where(
            ChannelOrder.organization_id == organization_id,
            ChannelOrder.channel_type == channel_type,
            ChannelOrder.remote_order_id == str(remote_order_id),
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            logger.info(f"Order {remote_order_id} from {channel_type} already exists. Skipping duplicate ingestion.")
            return existing, False

        order_dt = order_date or datetime.datetime.now(datetime.timezone.utc)
        resolved_lifecycle = order_lifecycle_status or ("paid" if financial_status == "paid" else "pending_payment")

        # 2. Create ChannelOrder
        order = ChannelOrder(
            organization_id=organization_id,
            channel_connection_id=channel_connection_id,
            channel_type=channel_type,
            remote_order_id=str(remote_order_id),
            order_number=str(order_number),
            customer_email=customer_email,
            customer_name=customer_name,
            total_amount=total_amount,
            subtotal=subtotal or total_amount,
            discount_amount=discount_amount,
            shipping_amount=shipping_amount,
            tax_amount=tax_amount,
            refund_amount=0.0,
            currency=currency,
            financial_status=financial_status,
            fulfillment_status=fulfillment_status,
            order_lifecycle_status=resolved_lifecycle,
            order_date=order_dt,
            shipping_address=shipping_address or {},
            billing_address=billing_address or {},
            inventory_synced=False,
            sync_status="synced",
            raw_payload=raw_payload or {},
        )
        db.add(order)
        await db.flush()

        # 3. Process line items and reconcile stock with inventory ledger
        items_to_sync_skus: List[Tuple[str, int]] = []

        for item in items_data:
            sku = (item.get("sku") or "").strip()
            qty = int(item.get("quantity") or 1)
            unit_price = float(item.get("unit_price") or item.get("price") or 0.0)
            total_price = float(item.get("total_price") or (unit_price * qty))
            title = item.get("title") or item.get("name") or "Ordered Item"
            ext_sku = item.get("external_sku") or sku
            ext_prod_id = item.get("remote_product_id") or item.get("external_product_id")
            ext_var_id = item.get("remote_variant_id") or item.get("external_variant_id")

            # Match SKU against master Product or ProductVariant
            prod_id = None
            variant_id = None
            mapping_status = "unmapped"

            if sku:
                # First check ProductVariant
                v_res = await db.execute(
                    select(ProductVariant)
                    .join(Product)
                    .where(
                        Product.organization_id == organization_id,
                        ProductVariant.sku == sku,
                    )
                )
                variant = v_res.scalar_one_or_none()
                if variant:
                    variant_id = variant.id
                    prod_id = variant.product_id
                    mapping_status = "mapped"
                    variant.stock_quantity = max(0, (variant.stock_quantity or 0) - qty)
                    p_parent = await db.get(Product, variant.product_id)
                    if p_parent:
                        p_parent.stock_quantity = max(0, (p_parent.stock_quantity or 0) - qty)
                else:
                    # Check Master Product SKU
                    p_res = await db.execute(
                        select(Product)
                        .options(selectinload(Product.variants))
                        .where(
                            Product.organization_id == organization_id,
                            Product.sku == sku,
                        )
                    )
                    product = p_res.scalar_one_or_none()
                    if product:
                        prod_id = product.id
                        mapping_status = "mapped"
                        product.stock_quantity = max(0, (product.stock_quantity or 0) - qty)
                        # If product has variants, attach primary variant
                        if product.variants:
                            variant_id = product.variants[0].id
                            product.variants[0].stock_quantity = max(0, (product.variants[0].stock_quantity or 0) - qty)

            # Channel-aware reservation policy: paid or confirmed COD; temporary reservation for pending
            should_reserve, is_temp, _ = ReservationPolicy.evaluate_reservation_need(
                financial_status=financial_status,
                payment_gateway=str(raw_payload.get("gateway") or "") if raw_payload else None,
                channel_type=channel_type,
            )
            if variant_id and should_reserve:
                try:
                    stock_level, _ = await InventoryService.record_movement(
                        db=db,
                        organization_id=organization_id,
                        product_variant_id=variant_id,
                        movement_type="order_reservation",
                        quantity_change=qty,
                        source_type="channel_order",
                        source_id=str(order.id),
                        notes=f"Order reservation for {channel_type} #{order_number}",
                    )
                    items_to_sync_skus.append((sku, stock_level.available_to_sell))
                except Exception as e:
                    logger.warning(f"Could not reserve stock for SKU {sku}: {e}")

            order_item = ChannelOrderItem(
                order_id=order.id,
                product_id=prod_id,
                product_variant_id=variant_id,
                sku=sku or "NO_SKU",
                external_sku=ext_sku,
                external_product_id=ext_prod_id,
                external_variant_id=ext_var_id,
                title=title,
                quantity=qty,
                unit_price=unit_price,
                total_price=total_price,
                discount_amount=float(item.get("discount_amount") or 0.0),
                tax_amount=float(item.get("tax_amount") or 0.0),
                returned_quantity=0,
                mapping_status=mapping_status,
            )
            db.add(order_item)

        order.inventory_synced = True
        await db.flush()

        # 4. Propagate stock decrement to all OTHER active connected channels
        if items_to_sync_skus:
            await OrderSyncService.queue_cross_channel_stock_sync(
                db=db,
                organization_id=organization_id,
                source_channel=channel_type,
                items_stock=items_to_sync_skus,
            )

        # 5. Audit log
        audit = AuditLog(
            organization_id=organization_id,
            action="ORDER_INGESTED_INVENTORY_SYNCED",
            resource_type="channel_order",
            resource_id=str(order.id),
            metadata_json={
                "channel": channel_type,
                "remote_order_id": remote_order_id,
                "order_number": order_number,
                "total_amount": total_amount,
                "items_count": len(items_data),
            },
        )
        db.add(audit)
        await db.commit()

        return order, True

    @staticmethod
    async def fulfill_order(
        db: AsyncSession,
        organization_id: uuid.UUID,
        order_id: uuid.UUID,
        carrier: str,
        tracking_number: str,
        tracking_url: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
    ) -> ChannelOrder:
        """Marks an order fulfilled, records tracking, and records order_fulfillment ledger movement."""
        stmt = (
            select(ChannelOrder)
            .options(selectinload(ChannelOrder.items))
            .where(ChannelOrder.organization_id == organization_id, ChannelOrder.id == order_id)
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found.")

        order.fulfillment_status = "fulfilled"
        order.order_lifecycle_status = "shipped"
        order.carrier = carrier
        order.tracking_number = tracking_number
        order.tracking_url = tracking_url
        order.last_external_update_at = datetime.datetime.now(datetime.timezone.utc)

        # Record order_fulfillment in inventory ledger
        for item in order.items:
            if item.product_variant_id:
                try:
                    await InventoryService.record_movement(
                        db=db,
                        organization_id=organization_id,
                        product_variant_id=item.product_variant_id,
                        movement_type="order_fulfillment",
                        quantity_change=item.quantity,
                        source_type="fulfillment",
                        source_id=str(order.id),
                        actor_id=actor_id,
                        notes=f"Shipped via {carrier} ({tracking_number})",
                    )
                except Exception as e:
                    logger.warning(f"Error recording fulfillment ledger for item {item.id}: {e}")

        audit = AuditLog(
            organization_id=organization_id,
            action="ORDER_FULFILLED",
            resource_type="channel_order",
            resource_id=str(order.id),
            metadata_json={"carrier": carrier, "tracking_number": tracking_number},
        )
        db.add(audit)
        await db.commit()
        return order

    @staticmethod
    async def cancel_order(
        db: AsyncSession,
        organization_id: uuid.UUID,
        order_id: uuid.UUID,
        reason: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
    ) -> ChannelOrder:
        """Cancels an order and releases reserved stock back to available_to_sell."""
        stmt = (
            select(ChannelOrder)
            .options(selectinload(ChannelOrder.items))
            .where(ChannelOrder.organization_id == organization_id, ChannelOrder.id == order_id)
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found.")

        order.fulfillment_status = "cancelled"
        order.order_lifecycle_status = "cancelled"
        order.cancellation_reason = reason or "Cancelled by customer/admin"
        order.last_external_update_at = datetime.datetime.now(datetime.timezone.utc)

        # Release reserved stock
        for item in order.items:
            if item.product_variant_id:
                try:
                    await InventoryService.record_movement(
                        db=db,
                        organization_id=organization_id,
                        product_variant_id=item.product_variant_id,
                        movement_type="cancellation_release",
                        quantity_change=item.quantity,
                        source_type="order_cancellation",
                        source_id=str(order.id),
                        actor_id=actor_id,
                        notes=f"Stock released due to cancellation: {reason}",
                    )
                except Exception as e:
                    logger.warning(f"Error releasing stock for item {item.id}: {e}")

        audit = AuditLog(
            organization_id=organization_id,
            action="ORDER_CANCELLED",
            resource_type="channel_order",
            resource_id=str(order.id),
            metadata_json={"reason": reason},
        )
        db.add(audit)
        await db.commit()
        return order

    @staticmethod
    async def refund_order(
        db: AsyncSession,
        organization_id: uuid.UUID,
        order_id: uuid.UUID,
        refund_amount: float,
        restock_items: bool = False,
        reason: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
    ) -> ChannelOrder:
        """Processes an order refund, records refund amount, and optionally restocks goods."""
        stmt = (
            select(ChannelOrder)
            .options(selectinload(ChannelOrder.items))
            .where(ChannelOrder.organization_id == organization_id, ChannelOrder.id == order_id)
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found.")

        cur_refund = Decimal(str(order.refund_amount or 0.0))
        ref_add = Decimal(str(refund_amount or 0.0))
        order.refund_amount = cur_refund + ref_add
        tot_amt = Decimal(str(order.total_amount or 0.0))
        if order.refund_amount >= tot_amt:
            order.financial_status = "refunded"
            order.order_lifecycle_status = "refunded"
        else:
            order.financial_status = "partially_refunded"
            order.order_lifecycle_status = "partially_refunded"

        order.last_external_update_at = datetime.datetime.now(datetime.timezone.utc)

        if restock_items:
            for item in order.items:
                if item.product_variant_id:
                    try:
                        await InventoryService.record_movement(
                            db=db,
                            organization_id=organization_id,
                            product_variant_id=item.product_variant_id,
                            movement_type="customer_return",
                            quantity_change=item.quantity,
                            source_type="order_refund_restock",
                            source_id=str(order.id),
                            actor_id=actor_id,
                            notes=f"Restocked upon refund: {reason}",
                        )
                    except Exception as e:
                        logger.warning(f"Error restocking item {item.id}: {e}")

        audit = AuditLog(
            organization_id=organization_id,
            action="ORDER_REFUNDED",
            resource_type="channel_order",
            resource_id=str(order.id),
            metadata_json={"refund_amount": refund_amount, "restocked": restock_items, "reason": reason},
        )
        db.add(audit)
        await db.commit()
        return order

    @staticmethod
    async def queue_cross_channel_stock_sync(
        db: AsyncSession,
        organization_id: uuid.UUID,
        source_channel: str,
        items_stock: List[Tuple[str, int]],
    ) -> int:
        """Queues stock synchronization jobs to all other connected active channels."""
        conns_res = await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.organization_id == organization_id,
                ChannelConnection.status == "active",
                ChannelConnection.channel_type != source_channel,
            )
        )
        connections = conns_res.scalars().all()
        jobs_queued = 0

        for conn in connections:
            for sku, stock in items_stock:
                p_res = await db.execute(
                    select(Product).where(
                        Product.organization_id == organization_id,
                        Product.sku == sku,
                    )
                )
                prod = p_res.scalar_one_or_none()
                if not prod:
                    continue

                idempotency_key = f"sync_stock_{conn.id}_{sku}_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
                job = PublishingJob(
                    organization_id=organization_id,
                    product_id=prod.id,
                    channel_connection_id=conn.id,
                    idempotency_key=idempotency_key,
                    job_type="sync_inventory",
                    status="queued",
                    payload_snapshot={"sku": sku, "new_stock_quantity": stock, "source": f"order_from_{source_channel}"},
                )
                db.add(job)
                jobs_queued += 1

        return jobs_queued

    @staticmethod
    async def sync_channel_orders(
        db: AsyncSession,
        organization_id: uuid.UUID,
        channel_type: str,
    ) -> Dict[str, Any]:
        """Polls remote channel orders API and ingests new orders with deduplication."""
        # Find active connection
        c_res = await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.organization_id == organization_id,
                ChannelConnection.channel_type == channel_type,
                ChannelConnection.status == "active",
            )
        )
        connection = c_res.scalar_one_or_none()
        if not connection:
            return {"status": "error", "message": f"Channel {channel_type} is not connected or active."}

        ingested_count = 0

        if channel_type == "woocommerce":
            wc = WooCommerceService()
            orders = await wc.get_orders(limit=25)
            for raw_ord in orders:
                items = [
                    {
                        "sku": item.get("sku") or f"WC_SKU_{item.get('product_id')}",
                        "title": item.get("name"),
                        "quantity": item.get("quantity", 1),
                        "unit_price": float(item.get("price") or 0.0),
                        "total_price": float(item.get("total") or 0.0),
                    }
                    for item in raw_ord.get("line_items", [])
                ]
                _, is_new = await OrderSyncService.ingest_order(
                    db=db,
                    organization_id=organization_id,
                    channel_type="woocommerce",
                    remote_order_id=str(raw_ord.get("id")),
                    order_number=str(raw_ord.get("number") or raw_ord.get("id")),
                    total_amount=float(raw_ord.get("total", 0.0)),
                    currency=raw_ord.get("currency", "INR"),
                    items_data=items,
                    channel_connection_id=connection.id,
                    customer_email=raw_ord.get("billing", {}).get("email"),
                    customer_name=f"{raw_ord.get('billing', {}).get('first_name', '')} {raw_ord.get('billing', {}).get('last_name', '')}".strip(),
                    financial_status=raw_ord.get("status", "completed"),
                    fulfillment_status="unfulfilled",
                    shipping_address=raw_ord.get("shipping") or {},
                    billing_address=raw_ord.get("billing") or {},
                )
                if is_new:
                    ingested_count += 1

        elif channel_type == "shopify":
            token = connection.encrypted_access_token
            shop = connection.account_name or "store.myshopify.com"
            try:
                res = await ShopifyService.get_orders(shop, token, limit=25)
                for ord_data in res.get("orders", []):
                    _, is_new = await OrderSyncService.ingest_order(
                        db=db,
                        organization_id=organization_id,
                        channel_type="shopify",
                        remote_order_id=ord_data.get("remote_order_id"),
                        order_number=ord_data.get("order_number"),
                        total_amount=ord_data.get("total_amount", 0.0),
                        currency=ord_data.get("currency", "INR"),
                        items_data=ord_data.get("items", []),
                        channel_connection_id=connection.id,
                        customer_email=ord_data.get("customer_email"),
                        customer_name=ord_data.get("customer_name"),
                        financial_status=ord_data.get("financial_status", "paid"),
                        fulfillment_status=ord_data.get("fulfillment_status", "unfulfilled"),
                        subtotal=ord_data.get("total_amount", 0.0),
                        discount_amount=ord_data.get("discount_amount", 0.0),
                        shipping_amount=ord_data.get("shipping_amount", 0.0),
                        tax_amount=ord_data.get("tax_amount", 0.0),
                        shipping_address=ord_data.get("shipping_address") or {},
                    )
                    if is_new:
                        ingested_count += 1
            except Exception as e:
                logger.warning(f"Error fetching Shopify orders during sync: {e}")

        return {
            "status": "success",
            "channel": channel_type,
            "new_orders_ingested": ingested_count,
            "synced_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    @staticmethod
    async def sync_all_channels(db: AsyncSession, organization_id: uuid.UUID) -> Dict[str, Any]:
        """Synchronizes orders across all active connected sales channels."""
        stmt = select(ChannelConnection).where(
            ChannelConnection.organization_id == organization_id,
            ChannelConnection.status == "active",
        )
        res = await db.execute(stmt)
        connections = res.scalars().all()
        synced = []
        total_ingested = 0
        notes = []

        for conn in connections:
            try:
                res_sync = await OrderSyncService.sync_channel_orders(db, organization_id, conn.channel_type)
                synced.append(conn.channel_type)
                total_ingested += res_sync.get("new_orders_ingested", 0)
                notes.append(f"Synced {conn.channel_type}: {res_sync.get('new_orders_ingested', 0)} new orders.")
            except Exception as e:
                notes.append(f"Sync error for {conn.channel_type}: {str(e)}")

        if not synced:
            notes.append("No active external channels connected.")

        return {
            "synced_channels": synced,
            "orders_ingested": total_ingested,
            "inventory_updates_queued": len(synced),
            "notes": notes,
        }

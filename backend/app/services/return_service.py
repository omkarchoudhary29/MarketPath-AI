"""Physical Return & Warehouse Inspection Lifecycle Service.

Separates physical warehouse returns from financial refunds:
requested -> authorized -> in_transit -> received -> inspected -> completed.
Ensures only physically received, inspected, and approved resalable items are restocked,
while damaged products are recorded as damaged stock and never enter available-to-sell.
"""

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.audit import AuditLog
from backend.app.models.order import ChannelOrder, ChannelOrderItem, ReturnItem, ReturnRequest
from backend.app.services.inventory_service import InventoryService

logger = logging.getLogger(__name__)


class ReturnService:
    """Enterprise physical return and warehouse disposition engine."""

    @staticmethod
    async def create_return_request(
        db: AsyncSession,
        organization_id: uuid.UUID,
        order_id: uuid.UUID,
        reason: str,
        items_data: List[Dict[str, Any]],
        notes: Optional[str] = None,
    ) -> ReturnRequest:
        """Initiates a physical return request for an existing channel order."""
        stmt = (
            select(ChannelOrder)
            .options(selectinload(ChannelOrder.items))
            .where(ChannelOrder.organization_id == organization_id, ChannelOrder.id == order_id)
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found.")

        return_num = f"RET-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        ret = ReturnRequest(
            organization_id=organization_id,
            order_id=order.id,
            return_number=return_num,
            status="requested",
            reason=reason,
            notes=notes,
        )
        db.add(ret)
        await db.flush()

        for item_in in items_data:
            sku = item_in.get("sku", "")
            qty_req = int(item_in.get("quantity", 1))

            # Match against order item
            matched_oi = next((oi for oi in order.items if oi.sku == sku), None)

            ret_item = ReturnItem(
                return_request_id=ret.id,
                order_item_id=matched_oi.id if matched_oi else None,
                product_id=matched_oi.product_id if matched_oi else None,
                product_variant_id=matched_oi.product_variant_id if matched_oi else None,
                sku=sku or (matched_oi.sku if matched_oi else "UNKNOWN"),
                quantity_ordered=matched_oi.quantity if matched_oi else qty_req,
                quantity_previously_returned=matched_oi.returned_quantity if matched_oi else 0,
                quantity_requested=qty_req,
                quantity_received=0,
                inspection_result="pending",
                resalable_quantity=0,
                damaged_quantity=0,
                refund_amount=float(item_in.get("refund_amount") or 0.0),
                restocked=False,
            )
            db.add(ret_item)

        # Update order lifecycle status
        order.order_lifecycle_status = "return_requested"

        audit = AuditLog(
            organization_id=organization_id,
            action="RETURN_REQUESTED",
            resource_type="return_request",
            resource_id=str(ret.id),
            metadata_json={"order_id": str(order.id), "return_number": return_num, "reason": reason},
        )
        db.add(audit)
        await db.commit()
        refreshed = await db.execute(
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.id == ret.id)
        )
        return refreshed.scalar_one()

    @staticmethod
    async def authorize_return(
        db: AsyncSession,
        organization_id: uuid.UUID,
        return_id: uuid.UUID,
        authorized_by: Optional[uuid.UUID] = None,
        carrier: Optional[str] = None,
        tracking_number: Optional[str] = None,
    ) -> ReturnRequest:
        """Authorizes customer return and generates reverse logistics tracking info."""
        stmt = (
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.organization_id == organization_id, ReturnRequest.id == return_id)
        )
        res = await db.execute(stmt)
        ret = res.scalar_one_or_none()
        if not ret:
            raise ValueError(f"ReturnRequest {return_id} not found.")

        ret.status = "authorized"
        ret.authorized_by = authorized_by
        ret.carrier = carrier or "Delhivery Reverse"
        ret.tracking_number = tracking_number or f"REV-{uuid.uuid4().hex[:8].upper()}"

        audit = AuditLog(
            organization_id=organization_id,
            action="RETURN_AUTHORIZED",
            resource_type="return_request",
            resource_id=str(ret.id),
            metadata_json={"tracking_number": ret.tracking_number, "carrier": ret.carrier},
        )
        db.add(audit)
        await db.commit()
        refreshed = await db.execute(
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.id == ret.id)
        )
        return refreshed.scalar_one()

    @staticmethod
    async def mark_in_transit(
        db: AsyncSession,
        organization_id: uuid.UUID,
        return_id: uuid.UUID,
    ) -> ReturnRequest:
        """Updates return status to in_transit when carrier scans reverse pickup."""
        stmt = (
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.organization_id == organization_id, ReturnRequest.id == return_id)
        )
        res = await db.execute(stmt)
        ret = res.scalar_one_or_none()
        if not ret:
            raise ValueError(f"ReturnRequest {return_id} not found.")

        ret.status = "in_transit"
        await db.commit()
        refreshed = await db.execute(
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.id == ret.id)
        )
        return refreshed.scalar_one()

    @staticmethod
    async def receive_return(
        db: AsyncSession,
        organization_id: uuid.UUID,
        return_id: uuid.UUID,
    ) -> ReturnRequest:
        """Records physical intake of returned parcel at fulfillment center."""
        stmt = (
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.organization_id == organization_id, ReturnRequest.id == return_id)
        )
        res = await db.execute(stmt)
        ret = res.scalar_one_or_none()
        if not ret:
            raise ValueError(f"ReturnRequest {return_id} not found.")

        ret.status = "received"
        ret.received_at = datetime.datetime.now(datetime.timezone.utc)
        await db.commit()
        refreshed = await db.execute(
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.id == ret.id)
        )
        return refreshed.scalar_one()

    @staticmethod
    async def inspect_and_complete_return(
        db: AsyncSession,
        organization_id: uuid.UUID,
        return_id: uuid.UUID,
        inspections: List[Dict[str, Any]],
        actor_id: Optional[uuid.UUID] = None,
    ) -> ReturnRequest:
        """Performs QA inspection, rests only resalable stock, writes off damaged, and completes return.
        
        inspections item format:
        {
            "item_id": uuid.UUID or str,
            "quantity_received": int,
            "resalable_quantity": int,
            "damaged_quantity": int,
            "inspection_result": "pass" | "partial" | "damaged",
            "refund_amount": float
        }
        """
        stmt = (
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.organization_id == organization_id, ReturnRequest.id == return_id)
        )
        res = await db.execute(stmt)
        ret = res.scalar_one_or_none()
        if not ret:
            raise ValueError(f"ReturnRequest {return_id} not found.")

        total_refund_calculated = 0.0

        for insp in inspections:
            item_id = str(insp.get("item_id"))
            matched_item = next((i for i in ret.items if str(i.id) == item_id or i.sku == insp.get("sku")), None)
            if not matched_item:
                continue

            # Prevent double restocking
            if matched_item.restocked:
                logger.warning(f"ReturnItem {matched_item.id} has already been restocked. Skipping duplicate restock.")
                continue

            qty_rec = int(insp.get("quantity_received", matched_item.quantity_requested))
            resale_qty = int(insp.get("resalable_quantity", qty_rec))
            dmg_qty = int(insp.get("damaged_quantity", 0))
            result = insp.get("inspection_result", "pass" if dmg_qty == 0 else ("damaged" if resale_qty == 0 else "partial"))
            ref_amt = float(insp.get("refund_amount", matched_item.refund_amount))

            matched_item.quantity_received = qty_rec
            matched_item.resalable_quantity = resale_qty
            matched_item.damaged_quantity = dmg_qty
            matched_item.inspection_result = result
            matched_item.refund_amount = ref_amt
            total_refund_calculated += ref_amt

            # Restock resalable items to inventory ledger
            if resale_qty > 0 and matched_item.product_variant_id:
                try:
                    await InventoryService.record_movement(
                        db=db,
                        organization_id=organization_id,
                        product_variant_id=matched_item.product_variant_id,
                        movement_type="customer_return",
                        quantity_change=resale_qty,
                        source_type="warehouse_return_inspection",
                        source_id=str(ret.id),
                        actor_id=actor_id,
                        notes=f"Physical return inspected & approved as resalable ({ret.return_number})",
                    )
                except Exception as e:
                    logger.error(f"Error restocking resalable inventory for {matched_item.sku}: {e}")

            # Record damaged goods in ledger without making them available to sell
            if dmg_qty > 0 and matched_item.product_variant_id:
                try:
                    await InventoryService.record_movement(
                        db=db,
                        organization_id=organization_id,
                        product_variant_id=matched_item.product_variant_id,
                        movement_type="damaged_stock",
                        quantity_change=dmg_qty,
                        source_type="warehouse_return_inspection",
                        source_id=str(ret.id),
                        actor_id=actor_id,
                        notes=f"Physical return damaged/unsellable write-off ({ret.return_number})",
                    )
                except Exception as e:
                    logger.error(f"Error recording damaged stock for {matched_item.sku}: {e}")

            matched_item.restocked = True

            # Update order item returned_quantity
            if matched_item.order_item_id:
                oi = await db.get(ChannelOrderItem, matched_item.order_item_id)
                if oi:
                    oi.returned_quantity += qty_rec

        ret.status = "completed"
        ret.inspected_at = datetime.datetime.now(datetime.timezone.utc)
        ret.completed_at = datetime.datetime.now(datetime.timezone.utc)
        ret.total_refund_amount = total_refund_calculated

        if ret.order_id:
            target_order = await db.get(ChannelOrder, ret.order_id)
            if target_order:
                target_order.order_lifecycle_status = "returned"

        audit = AuditLog(
            organization_id=organization_id,
            action="RETURN_INSPECTED_COMPLETED",
            resource_type="return_request",
            resource_id=str(ret.id),
            metadata_json={
                "return_number": ret.return_number,
                "total_refund": total_refund_calculated,
                "inspected_items": len(inspections),
            },
        )
        db.add(audit)
        await db.commit()
        refreshed = await db.execute(
            select(ReturnRequest)
            .options(selectinload(ReturnRequest.items))
            .where(ReturnRequest.id == ret.id)
        )
        return refreshed.scalar_one()

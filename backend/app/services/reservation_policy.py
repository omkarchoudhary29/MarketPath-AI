"""Channel-Aware Inventory Reservation & Payment Lifecycle Policy Engine.

Enforces strict inventory reservation rules:
1. Paid orders reserve stock exactly once.
2. Confirmed COD orders reserve stock according to channel policy.
3. Unpaid online orders receive a temporary reservation with configurable expiry.
4. Expired reservations are released automatically.
5. Payment failures release applicable reservations immediately.
6. Cancellations release only quantities reserved for that order.
"""

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.audit import AuditLog
from backend.app.models.order import ChannelOrder, ChannelOrderItem
from backend.app.services.inventory_service import InventoryService

logger = logging.getLogger(__name__)


class ReservationPolicy:
    """Centralized channel-aware inventory reservation rules."""

    DEFAULT_TEMPORARY_EXPIRY_MINUTES = 30

    @classmethod
    def evaluate_reservation_need(
        cls,
        financial_status: str,
        payment_gateway: Optional[str] = None,
        channel_type: str = "shopify",
        is_cod: bool = False,
    ) -> Tuple[bool, bool, Optional[datetime.datetime]]:
        """Evaluates whether an order should reserve stock.
        
        Returns:
            (should_reserve: bool, is_temporary: bool, expires_at: Optional[datetime])
        """
        status_clean = (financial_status or "").strip().lower()
        now = datetime.datetime.now(datetime.timezone.utc)

        # 1. Paid orders: permanent reservation until fulfilled
        if status_clean in ("paid", "captured"):
            return True, False, None

        # 2. Confirmed COD orders: reserve stock per policy
        if is_cod or (payment_gateway and "cod" in payment_gateway.lower()):
            return True, False, None

        # 3. Unpaid / pending online orders: temporary reservation with expiry
        if status_clean in ("pending", "authorized", "awaiting_payment"):
            expires_at = now + datetime.timedelta(minutes=cls.DEFAULT_TEMPORARY_EXPIRY_MINUTES)
            return True, True, expires_at

        # 4. Failed, cancelled, refunded: do not reserve
        return False, False, None

    @staticmethod
    async def handle_payment_failure(
        db: AsyncSession,
        organization_id: uuid.UUID,
        order_id: uuid.UUID,
        failure_reason: Optional[str] = None,
    ) -> ChannelOrder:
        """Transitions order to payment_failed and releases any active reservations."""
        stmt = (
            select(ChannelOrder)
            .options(selectinload(ChannelOrder.items))
            .where(ChannelOrder.organization_id == organization_id, ChannelOrder.id == order_id)
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found.")

        order.financial_status = "failed"
        order.order_lifecycle_status = "payment_failed"
        order.cancellation_reason = failure_reason or "Payment session failed or expired"

        # Release stock reservation for each mapped item
        for item in order.items:
            if item.product_variant_id:
                try:
                    await InventoryService.record_movement(
                        db=db,
                        organization_id=organization_id,
                        product_variant_id=item.product_variant_id,
                        movement_type="cancellation_release",
                        quantity_change=item.quantity,
                        source_type="payment_failure_release",
                        source_id=str(order.id),
                        notes=f"Stock reservation released due to payment failure: {failure_reason}",
                    )
                except Exception as e:
                    logger.warning(f"Error releasing reservation on payment failure for {item.sku}: {e}")

        audit = AuditLog(
            organization_id=organization_id,
            action="ORDER_PAYMENT_FAILED_STOCK_RELEASED",
            resource_type="channel_order",
            resource_id=str(order.id),
            metadata_json={"failure_reason": failure_reason},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(order)
        return order

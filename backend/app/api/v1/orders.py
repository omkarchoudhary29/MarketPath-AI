"""API Router for Orders and Inventory Synchronization."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.models.order import ChannelOrder, ChannelOrderItem
from backend.app.schemas.order import (
    OrderCancelRequest,
    OrderFulfillRequest,
    OrderListResponse,
    OrderRead,
    OrderRefundRequest,
    OrderSyncRequest,
    OrderSyncResponse,
)
from backend.app.services.order_sync_service import OrderSyncService

router = APIRouter()


@router.get("", response_model=OrderListResponse)
async def list_orders(
    channel_type: Optional[str] = Query(None, description="Filter by channel type (shopify, woocommerce, amazon, flipkart)"),
    financial_status: Optional[str] = Query(None, description="Filter by financial status (paid, pending, refunded)"),
    fulfillment_status: Optional[str] = Query(None, description="Filter by fulfillment status (fulfilled, unfulfilled, cancelled)"),
    order_lifecycle_status: Optional[str] = Query(None, description="Filter by lifecycle status (new, processing, shipped, delivered, cancelled)"),
    search: Optional[str] = Query(None, description="Search by order number or customer name"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists omnichannel sales orders for the active tenant."""
    query = (
        select(ChannelOrder)
        .options(selectinload(ChannelOrder.items))
        .where(ChannelOrder.organization_id == context.organization_id)
    )

    if channel_type:
        query = query.where(ChannelOrder.channel_type == channel_type)
    if financial_status:
        query = query.where(ChannelOrder.financial_status == financial_status)
    if fulfillment_status:
        query = query.where(ChannelOrder.fulfillment_status == fulfillment_status)
    if order_lifecycle_status:
        query = query.where(ChannelOrder.order_lifecycle_status == order_lifecycle_status)
    if search:
        query = query.where(
            (ChannelOrder.order_number.ilike(f"%{search}%"))
            | (ChannelOrder.customer_name.ilike(f"%{search}%"))
            | (ChannelOrder.customer_email.ilike(f"%{search}%"))
        )

    query = query.order_by(desc(ChannelOrder.order_date)).limit(limit).offset(offset)
    res = await db.execute(query)
    orders = res.scalars().all()

    # Total counts and revenue
    total_q = select(func.count(ChannelOrder.id)).where(ChannelOrder.organization_id == context.organization_id)
    rev_q = select(func.sum(ChannelOrder.total_amount)).where(
        ChannelOrder.organization_id == context.organization_id,
        ChannelOrder.financial_status == "paid",
    )

    total_orders = (await db.execute(total_q)).scalar() or 0
    total_revenue = float((await db.execute(rev_q)).scalar() or 0.0)

    return OrderListResponse(
        total_orders=total_orders,
        total_revenue_inr=total_revenue,
        orders=[OrderRead.model_validate(o) for o in orders],
    )


@router.get("/{order_id}", response_model=OrderRead)
async def get_order_detail(
    order_id: uuid.UUID,
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves order details with line items and fulfillment state."""
    stmt = (
        select(ChannelOrder)
        .options(selectinload(ChannelOrder.items))
        .where(
            ChannelOrder.id == order_id,
            ChannelOrder.organization_id == context.organization_id,
        )
    )
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found in this organization.")

    return OrderRead.model_validate(order)


@router.post("/{order_id}/fulfill", response_model=OrderRead)
async def fulfill_order(
    order_id: uuid.UUID,
    payload: OrderFulfillRequest,
    context: TenantContext = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Marks order fulfilled and records tracking details."""
    try:
        order = await OrderSyncService.fulfill_order(
            db=db,
            organization_id=context.organization_id,
            order_id=order_id,
            carrier=payload.carrier,
            tracking_number=payload.tracking_number,
            tracking_url=payload.tracking_url,
            actor_id=context.user.id if context.user else None,
        )
        return OrderRead.model_validate(order)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: uuid.UUID,
    payload: OrderCancelRequest,
    context: TenantContext = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Cancels order and releases reserved stock back to inventory."""
    try:
        order = await OrderSyncService.cancel_order(
            db=db,
            organization_id=context.organization_id,
            order_id=order_id,
            reason=payload.reason,
            actor_id=context.user.id if context.user else None,
        )
        return OrderRead.model_validate(order)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{order_id}/refund", response_model=OrderRead)
async def refund_order(
    order_id: uuid.UUID,
    payload: OrderRefundRequest,
    context: TenantContext = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Processes an order refund and optionally restocks items."""
    try:
        order = await OrderSyncService.refund_order(
            db=db,
            organization_id=context.organization_id,
            order_id=order_id,
            refund_amount=payload.refund_amount,
            restock_items=payload.restock_items,
            reason=payload.reason,
            actor_id=context.user.id if context.user else None,
        )
        return OrderRead.model_validate(order)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sync", response_model=OrderSyncResponse)
async def trigger_order_sync(
    payload: OrderSyncRequest,
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer"])),
    db: AsyncSession = Depends(get_db),
):
    """Triggers manual order and inventory sync across all connected sales channels."""
    if payload.channel_type:
        result = await OrderSyncService.sync_channel_orders(db, context.organization_id, payload.channel_type)
        return OrderSyncResponse(
            synced_channels=[payload.channel_type],
            orders_ingested=result.get("new_orders_ingested", 0),
            inventory_updates_queued=1,
            notes=[f"Synchronized orders from {payload.channel_type}."],
        )
    result = await OrderSyncService.sync_all_channels(db, context.organization_id)
    return OrderSyncResponse(
        synced_channels=result["synced_channels"],
        orders_ingested=result["orders_ingested"],
        inventory_updates_queued=result["inventory_updates_queued"],
        notes=result["notes"],
    )

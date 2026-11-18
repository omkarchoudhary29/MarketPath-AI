"""API Router for Unified Inventory and Auditable Stock Movement Ledger."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.services.inventory_service import InventoryService

router = APIRouter()


class StockAdjustRequest(BaseModel):
    product_variant_id: uuid.UUID
    quantity_change: int
    movement_type: str = "manual_adjustment"
    notes: Optional[str] = None


@router.get("")
async def get_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="all, low_stock, out_of_stock"),
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves paginated inventory summary with SKU-level distribution and stockout telemetry."""
    return await InventoryService.get_inventory_summary(
        db=db,
        organization_id=context.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        filter_status=status,
    )


@router.get("/movements")
async def get_inventory_movements(
    variant_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    context: TenantContext = Depends(require_role(["owner", "admin", "marketer", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves immutable auditable stock movement ledger entries."""
    return await InventoryService.get_movement_history(
        db=db,
        organization_id=context.organization_id,
        product_variant_id=variant_id,
        limit=limit,
    )


@router.post("/adjust")
async def adjust_inventory(
    payload: StockAdjustRequest,
    context: TenantContext = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Records manual inventory adjustment with row-locking and immutable audit ledger entry."""
    try:
        stock, ledger = await InventoryService.record_movement(
            db=db,
            organization_id=context.organization_id,
            product_variant_id=payload.product_variant_id,
            movement_type=payload.movement_type,
            quantity_change=payload.quantity_change,
            source_type="manual_adjustment",
            actor_id=context.user.id if context.user else None,
            notes=payload.notes,
        )
        await db.commit()
        return {
            "status": "success",
            "sku": stock.sku,
            "physical_stock": stock.physical_stock,
            "available_to_sell": stock.available_to_sell,
            "reserved_stock": stock.reserved_stock,
            "movement_id": str(ledger.id),
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

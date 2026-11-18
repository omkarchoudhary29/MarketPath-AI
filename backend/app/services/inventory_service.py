"""Unified Inventory & Auditable Stock Movement Ledger Service.

Provides concurrency-safe stock operations, row-level locking (with_for_update),
auditable ledger recording, cross-channel synchronization, and reconciliation.
"""

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.catalogue import Product, ProductVariant
from backend.app.models.channel import ChannelConnection, ChannelListing
from backend.app.models.inventory import InventoryLedger, StockLevel

logger = logging.getLogger(__name__)


class InsufficientStockError(Exception):
    """Raised when available stock is insufficient to fulfill reservation request."""
    pass


class InventoryService:
    """Core enterprise inventory management service."""

    @staticmethod
    async def get_or_create_stock_level(
        db: AsyncSession,
        organization_id: uuid.UUID,
        product_variant_id: uuid.UUID,
        location_id: str = "primary_warehouse",
    ) -> StockLevel:
        """Retrieves existing StockLevel or initializes a new one from ProductVariant."""
        res = await db.execute(
            select(StockLevel).where(
                StockLevel.organization_id == organization_id,
                StockLevel.product_variant_id == product_variant_id,
                StockLevel.location_id == location_id,
            )
        )
        stock = res.scalars().first()
        if stock:
            return stock

        # Fetch variant to get initial stock
        var_res = await db.execute(
            select(ProductVariant).where(ProductVariant.id == product_variant_id)
        )
        variant = var_res.scalars().first()
        if not variant:
            raise ValueError(f"ProductVariant {product_variant_id} not found.")

        initial_qty = int(variant.stock_quantity or 0)
        stock = StockLevel(
            organization_id=organization_id,
            product_id=variant.product_id,
            product_variant_id=variant.id,
            sku=variant.sku,
            location_id=location_id,
            physical_stock=initial_qty,
            reserved_stock=0,
            available_to_sell=initial_qty,
            committed_stock=0,
            damaged_stock=0,
            returned_stock=0,
            reorder_point=10,
        )
        db.add(stock)
        await db.flush()

        # Record initial ledger entry
        ledger = InventoryLedger(
            organization_id=organization_id,
            product_id=variant.product_id,
            product_variant_id=variant.id,
            sku=variant.sku,
            location_id=location_id,
            movement_type="initial_stock",
            quantity_change=initial_qty,
            previous_quantity=0,
            new_quantity=initial_qty,
            source_type="system_init",
            notes="Initial stock level established from variant definition.",
        )
        db.add(ledger)
        await db.flush()
        return stock

    @staticmethod
    async def record_movement(
        db: AsyncSession,
        organization_id: uuid.UUID,
        product_variant_id: uuid.UUID,
        movement_type: str,
        quantity_change: int,
        source_type: str = "manual",
        source_id: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
        location_id: str = "primary_warehouse",
    ) -> Tuple[StockLevel, InventoryLedger]:
        """Concurrency-safe inventory mutation with row-locking and immutable audit ledger."""
        # Row-level lock on StockLevel
        res = await db.execute(
            select(StockLevel)
            .where(
                StockLevel.organization_id == organization_id,
                StockLevel.product_variant_id == product_variant_id,
                StockLevel.location_id == location_id,
            )
            .with_for_update()
        )
        stock = res.scalars().first()
        if not stock:
            stock = await InventoryService.get_or_create_stock_level(
                db, organization_id, product_variant_id, location_id
            )

        prev_available = stock.available_to_sell

        if movement_type == "order_reservation":
            if stock.available_to_sell < quantity_change:
                raise InsufficientStockError(
                    f"Insufficient stock for SKU {stock.sku}. Requested: {quantity_change}, Available: {stock.available_to_sell}"
                )
            stock.reserved_stock += quantity_change
            stock.available_to_sell -= quantity_change
            new_available = stock.available_to_sell

        elif movement_type == "order_fulfillment":
            stock.reserved_stock = max(0, stock.reserved_stock - quantity_change)
            stock.physical_stock = max(0, stock.physical_stock - quantity_change)
            new_available = stock.available_to_sell

        elif movement_type == "cancellation_release":
            stock.reserved_stock = max(0, stock.reserved_stock - quantity_change)
            stock.available_to_sell += quantity_change
            new_available = stock.available_to_sell

        elif movement_type == "customer_return":
            stock.returned_stock += quantity_change
            stock.physical_stock += quantity_change
            stock.available_to_sell += quantity_change
            new_available = stock.available_to_sell

        elif movement_type == "restock" or movement_type == "manual_adjustment":
            stock.physical_stock += quantity_change
            stock.available_to_sell += quantity_change
            new_available = stock.available_to_sell

        elif movement_type == "damaged_stock":
            stock.damaged_stock += quantity_change
            if source_type != "warehouse_return_inspection":
                stock.physical_stock = max(0, stock.physical_stock - quantity_change)
                stock.available_to_sell = max(0, stock.available_to_sell - quantity_change)
            new_available = stock.available_to_sell

        else:
            stock.available_to_sell += quantity_change
            stock.physical_stock += quantity_change
            new_available = stock.available_to_sell

        # Keep ProductVariant stock in sync
        var_res = await db.execute(
            select(ProductVariant).where(ProductVariant.id == product_variant_id)
        )
        variant = var_res.scalars().first()
        if variant:
            variant.stock_quantity = stock.available_to_sell

        # Create audit ledger entry
        ledger = InventoryLedger(
            organization_id=organization_id,
            product_id=stock.product_id,
            product_variant_id=stock.product_variant_id,
            sku=stock.sku,
            location_id=location_id,
            movement_type=movement_type,
            quantity_change=quantity_change,
            previous_quantity=prev_available,
            new_quantity=new_available,
            source_type=source_type,
            source_id=source_id,
            actor_id=actor_id,
            notes=notes,
        )
        db.add(ledger)
        await db.flush()

        return stock, ledger

    @staticmethod
    async def get_inventory_summary(
        db: AsyncSession,
        organization_id: uuid.UUID,
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None,
        filter_status: Optional[str] = None,  # all, low_stock, out_of_stock
    ) -> Dict[str, Any]:
        """Returns paginated inventory summary with SKU details, drift indicators, and metrics."""
        offset = (page - 1) * page_size

        # Query variants joined with products
        query = (
            select(ProductVariant, Product)
            .join(Product, ProductVariant.product_id == Product.id)
            .where(Product.organization_id == organization_id)
        )

        if search:
            query = query.where(
                (ProductVariant.sku.ilike(f"%{search}%"))
                | (ProductVariant.title.ilike(f"%{search}%"))
                | (Product.title.ilike(f"%{search}%"))
            )

        total_res = await db.execute(select(func.count()).select_from(query.subquery()))
        total_count = total_res.scalar() or 0

        rows = (await db.execute(query.offset(offset).limit(page_size))).all()

        items = []
        for variant, product in rows:
            stock_res = await db.execute(
                select(StockLevel).where(
                    StockLevel.organization_id == organization_id,
                    StockLevel.product_variant_id == variant.id,
                )
            )
            stock = stock_res.scalars().first()
            avail = stock.available_to_sell if stock else variant.stock_quantity
            physical = stock.physical_stock if stock else variant.stock_quantity
            reserved = stock.reserved_stock if stock else 0

            # Determine status
            if avail <= 0:
                stock_status = "out_of_stock"
            elif avail <= 10:
                stock_status = "low_stock"
            else:
                stock_status = "in_stock"

            if filter_status and filter_status != "all" and stock_status != filter_status:
                continue

            items.append({
                "variant_id": str(variant.id),
                "product_id": str(product.id),
                "product_title": product.title,
                "variant_title": variant.title,
                "sku": variant.sku,
                "price": float(variant.price),
                "physical_stock": physical,
                "reserved_stock": reserved,
                "available_to_sell": avail,
                "reorder_point": stock.reorder_point if stock else 10,
                "status": stock_status,
                "last_updated": stock.updated_at.isoformat() if stock else datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })

        # Aggregates
        total_skus = total_count
        low_stock_count = sum(1 for i in items if i["status"] == "low_stock")
        out_of_stock_count = sum(1 for i in items if i["status"] == "out_of_stock")

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "metrics": {
                "total_skus": total_skus,
                "in_stock_skus": max(0, total_skus - low_stock_count - out_of_stock_count),
                "low_stock_skus": low_stock_count,
                "out_of_stock_skus": out_of_stock_count,
            },
        }

    @staticmethod
    async def get_movement_history(
        db: AsyncSession,
        organization_id: uuid.UUID,
        product_variant_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieves auditable ledger entries for stock movements."""
        query = (
            select(InventoryLedger)
            .where(InventoryLedger.organization_id == organization_id)
            .order_by(InventoryLedger.created_at.desc())
            .limit(limit)
        )
        if product_variant_id:
            query = query.where(InventoryLedger.product_variant_id == product_variant_id)

        rows = (await db.execute(query)).scalars().all()
        return [
            {
                "id": str(r.id),
                "sku": r.sku,
                "movement_type": r.movement_type,
                "quantity_change": r.quantity_change,
                "previous_quantity": r.previous_quantity,
                "new_quantity": r.new_quantity,
                "source_type": r.source_type,
                "source_id": r.source_id,
                "notes": r.notes,
                "timestamp": r.created_at.isoformat(),
            }
            for r in rows
        ]

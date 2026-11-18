"""PostgreSQL Real Concurrency Integration Test Suite.

Tests genuine PostgreSQL row-level locking (SELECT ... FOR UPDATE),
atomic inventory reservation, and concurrency safety.
Per Section 4 requirements:
If PostgreSQL cannot be reached at execution time, reports the test as BLOCKED.
Never counts it as passed without real PostgreSQL execution.
"""

import asyncio
import os
import uuid
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.models.inventory import InventoryLedger, StockLevel
from backend.app.services.inventory_service import InsufficientStockError, InventoryService

POSTGRES_TEST_URL = os.environ.get(
    "POSTGRES_TEST_DATABASE_URL",
    os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/marketpath_test")
)


async def check_postgres_available(url: str) -> bool:
    if not url.startswith("postgresql"):
        return False
    try:
        engine = create_async_engine(url, connect_args={"timeout": 3})
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False


@pytest.mark.asyncio
async def test_postgres_concurrent_orders_last_item():
    """Two simultaneous transactions requesting the last remaining item.
    Only one must succeed; the second must receive InsufficientStockError.
    """
    is_available = await check_postgres_available(POSTGRES_TEST_URL)
    if not is_available:
        pytest.skip(
            f"BLOCKED: PostgreSQL database not reachable at {POSTGRES_TEST_URL}. "
            "Section 4 requirement: If PostgreSQL cannot be reached, report the test as BLOCKED."
        )

    engine = create_async_engine(POSTGRES_TEST_URL, pool_size=5)
    SessionMaker = async_sessionmaker(engine, expire_on_commit=False)

    org_id = uuid.uuid4()
    var_id = uuid.uuid4()

    # 1. Setup single item in PostgreSQL
    async with SessionMaker() as init_session:
        stk = StockLevel(
            organization_id=org_id,
            product_id=uuid.uuid4(),
            product_variant_id=var_id,
            sku="PG-LAST-ITEM",
            location_id="primary_warehouse",
            physical_stock=1,
            reserved_stock=0,
            available_to_sell=1,
        )
        init_session.add(stk)
        await init_session.commit()

    # 2. Concurrently execute two reservations requesting 1 item each
    async def make_reservation(worker_id: int):
        async with SessionMaker() as session:
            try:
                await InventoryService.record_movement(
                    db=session,
                    organization_id=org_id,
                    product_variant_id=var_id,
                    movement_type="order_reservation",
                    quantity_change=1,
                    source_type="concurrent_order",
                    source_id=f"worker_{worker_id}",
                )
                await session.commit()
                return "SUCCESS"
            except InsufficientStockError:
                await session.rollback()
                return "OUT_OF_STOCK"
            except Exception as e:
                await session.rollback()
                return f"ERROR: {str(e)}"

    results = await asyncio.gather(make_reservation(1), make_reservation(2))

    # Assert exactly one succeeded and one was rejected due to lack of stock
    assert results.count("SUCCESS") == 1
    assert results.count("OUT_OF_STOCK") == 1

    # Verify final stock is 0 available, 1 reserved
    async with SessionMaker() as verify_session:
        res = await verify_session.execute(select(StockLevel).where(StockLevel.product_variant_id == var_id))
        final_stock = res.scalar_one()
        assert final_stock.available_to_sell == 0
        assert final_stock.reserved_stock == 1

    await engine.dispose()

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.models.billing import ServiceOrder
from backend.app.schemas.billing import ServiceCatalogItem, ServiceOrderCreate, ServiceOrderRead
from backend.app.services.billing_service import BillingService

router = APIRouter(prefix="/services", tags=["Managed Growth Services"])


@router.get("/catalog", response_model=List[ServiceCatalogItem])
async def list_service_catalog():
    """Lists available managed onboarding, photography, copywriting, and marketing services."""
    return BillingService.get_service_catalog()


@router.post("/orders", response_model=ServiceOrderRead, status_code=status.HTTP_201_CREATED)
async def request_managed_service(
    request: ServiceOrderCreate,
    context: TenantContext = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Submits a managed service request for operator quotation and fulfillment."""
    order = await BillingService.create_service_order(
        db=db,
        organization_id=context.organization_id,
        service_type=request.service_type,
        scope_description=request.scope_description,
        target_budget_inr=request.target_budget_inr,
        requirements=request.requirements,
        due_date=request.due_date,
    )
    return order


@router.get("/orders", response_model=List[ServiceOrderRead])
async def list_organization_service_orders(
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists all managed service requests submitted by the organization."""
    return await BillingService.get_service_orders(db, context.organization_id)


@router.get("/orders/{order_id}", response_model=ServiceOrderRead)
async def get_service_order_details(
    order_id: uuid.UUID,
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Returns details, operator assignments, and deliverables for a specific service order."""
    result = await db.execute(
        select(ServiceOrder).where(
            ServiceOrder.id == order_id,
            ServiceOrder.organization_id == context.organization_id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Managed service order not found.",
        )
    return order


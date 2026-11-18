import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.models.billing import Plan
from backend.app.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PaymentRead,
    PaymentVerifyRequest,
    PlanRead,
    SubscriptionRead,
    UsageStatsRead,
)
from backend.app.services.billing_service import BillingService
from backend.app.services.payment_service import PaymentService

router = APIRouter(prefix="/billing", tags=["Subscription Billing & Usage Quotas"])


@router.get("/plans", response_model=List[PlanRead])
async def list_available_plans(
    db: AsyncSession = Depends(get_db),
):
    """Lists all configurable SaaS pricing tiers (Starter, Growth, Scale)."""
    return await BillingService.get_active_plans(db)


@router.get("/subscription", response_model=SubscriptionRead)
async def get_current_subscription(
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Returns the tenant's active subscription tier, dates, and renewal status."""
    return await BillingService.get_or_create_tenant_subscription(db, context.organization_id)


@router.get("/usage", response_model=UsageStatsRead)
async def get_resource_usage(
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Returns real-time usage metrics against configured plan quotas."""
    return await BillingService.get_tenant_usage_stats(db, context.organization_id)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_order(
    request: CheckoutRequest,
    context: TenantContext = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Initiates payment order with the selected payment gateway (Razorpay or Cashfree)."""
    plan_res = await db.execute(select(Plan).where(Plan.id == request.plan_id))
    plan = plan_res.scalar_one_or_none()
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found or inactive.",
        )

    gateway = PaymentService.get_gateway(request.gateway)
    receipt_id = f"rcpt_{context.organization_id.hex[:8]}_{int(uuid.uuid4().time_low)}"
    order_data = gateway.create_order(
        amount_inr=float(plan.monthly_price_inr),
        currency="INR",
        receipt_id=receipt_id,
        notes={
            "organization_id": str(context.organization_id),
            "plan_id": str(plan.id),
            "plan_name": plan.name,
        },
    )

    return CheckoutResponse(
        order_id=order_data["order_id"],
        amount_inr=float(plan.monthly_price_inr),
        currency="INR",
        key_id=order_data["key_id"],
        gateway=request.gateway,
        plan_name=plan.name,
        organization_id=context.organization_id,
    )


@router.post("/verify", response_model=SubscriptionRead)
async def verify_payment_and_activate(
    request: PaymentVerifyRequest,
    context: TenantContext = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Server-side verification of payment signature. Activates subscription upon valid signature."""
    gateway = PaymentService.get_gateway(request.gateway)
    is_valid = gateway.verify_payment_signature(
        payment_id=request.payment_id,
        order_id=request.order_id,
        signature=request.signature,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment signature verification failed. Untrusted payment payload.",
        )

    if not request.plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing plan_id for subscription upgrade.",
        )

    plan_res = await db.execute(select(Plan).where(Plan.id == request.plan_id))
    plan = plan_res.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target plan not found.",
        )

    updated_sub = await BillingService.process_subscription_upgrade(
        db=db,
        organization_id=context.organization_id,
        plan_id=plan.id,
        payment_id=request.payment_id,
        order_id=request.order_id,
        amount_inr=float(plan.monthly_price_inr),
        gateway=request.gateway,
        actor_user_id=context.user.id,
    )

    return updated_sub


@router.post("/cancel", response_model=SubscriptionRead)
async def cancel_subscription(
    context: TenantContext = Depends(require_role(["owner"])),
    db: AsyncSession = Depends(get_db),
):
    """Cancels recurring subscription renewal at the end of the current billing period."""
    return await BillingService.cancel_subscription(
        db, context.organization_id, actor_user_id=context.user.id
    )


@router.get("/payments", response_model=List[PaymentRead])
async def list_payment_transactions(
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists billing payments and transaction receipts for the tenant."""
    return await BillingService.get_payment_history(db, context.organization_id)


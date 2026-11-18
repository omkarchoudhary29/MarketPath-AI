"""MarketPath AI — Dedicated Isolated Demo Admin Router.

Provides isolated, read-only demonstration telemetry and synthetic records
for recruiter demo exploration without granting platform superadmin privileges
or exposing real customer/tenant records.
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.agency import AgencyProfile
from backend.app.models.audit import AuditLog
from backend.app.models.billing import Payment, Plan, ServiceOrder, Subscription
from backend.app.models.catalogue import Product
from backend.app.models.channel import ChannelConnection, PublishingJob
from backend.app.models.consultation import ConsultationRequest
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import UserProfile
from backend.app.schemas.admin import (
    AdminJobRead,
    AdminOrgRead,
    AdminOverviewTelemetry,
    AdminUserRead,
)
from backend.app.schemas.billing import PlanRead, ServiceOrderRead

router = APIRouter(prefix="/demo-admin", tags=["Demo Administration (Isolated Read-Only)"])

DEMO_BRAND_ORG_ID = uuid.UUID("d0000002-0000-0000-0000-000000000001")
DEMO_AGENCY_ORG_ID = uuid.UUID("d0000002-0000-0000-0000-000000000002")

DEMO_EMAILS = {
    "demo.company@marketpath.ai",
    "demo.agency@marketpath.ai",
    "demo.consultant@marketpath.ai",
    "demo.admin@marketpath.ai",
}


async def require_demo_admin_access(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """Restricts access exclusively to authorized Demo Administrator or Platform Administrator."""
    if (current_user.email == "demo.admin@marketpath.ai" and current_user.account_type == "admin") or current_user.is_platform_admin:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Demo Operator or Platform Administrator privileges required.",
    )


# -----------------------------------------------------------------------------
# 1. System Overview Telemetry (Synthetic & Demo-Only Isolated Scope)
# -----------------------------------------------------------------------------

@router.get("/overview", response_model=AdminOverviewTelemetry)
async def get_demo_admin_overview(
    admin_user: UserProfile = Depends(require_demo_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Provides isolated demonstration telemetry for the Demo Administrator persona."""
    return AdminOverviewTelemetry(
        total_organizations=1,
        active_organizations=1,
        total_users=4,
        total_products=18,
        total_publishing_jobs=12,
        failed_publishing_jobs=0,
        publishing_success_rate=100.0,
        total_revenue_inr=450000.0,
        active_paid_subscribers=1,
        pending_service_orders=2,
        connector_health={
            "shopify_active_connections": 1,
            "instagram_active_connections": 1,
            "api_cluster_status": "HEALTHY (SYNTHETIC DEMO ENVIRONMENT)",
            "rate_limit_headroom": "99.2%",
            "environment_mode": "ISOLATED_RECRUITER_DEMO",
            "production_data_access": "BLOCKED",
        },
        operator_email=admin_user.email,
    )


# -----------------------------------------------------------------------------
# 2. Demo Organizations (Strictly Demo Brand / Agency)
# -----------------------------------------------------------------------------

@router.get("/organizations", response_model=List[AdminOrgRead])
async def list_demo_organizations(
    admin_user: UserProfile = Depends(require_demo_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Lists only synthetic demo organizations."""
    res = await db.execute(
        select(Organization)
        .options(selectinload(Organization.members))
        .where(Organization.id.in_([DEMO_BRAND_ORG_ID, DEMO_AGENCY_ORG_ID]))
    )
    orgs = res.scalars().all()
    out = []
    for o in orgs:
        sub_res = await db.execute(
            select(Subscription).options(selectinload(Subscription.plan)).where(Subscription.organization_id == o.id)
        )
        sub = sub_res.scalar_one_or_none()
        out.append(
            AdminOrgRead(
                id=o.id,
                name=o.name,
                slug=o.slug,
                is_active=o.is_active,
                plan_name=sub.plan.name if (sub and sub.plan) else "Growth Scale (Demo)",
                subscription_status=sub.status if sub else "active",
                products_count=18 if o.id == DEMO_BRAND_ORG_ID else 0,
                channels_count=2 if o.id == DEMO_BRAND_ORG_ID else 0,
                members_count=len(o.members) if o.members else 1,
                created_at=o.created_at,
            )
        )
    return out


# -----------------------------------------------------------------------------
# 3. Demo Users (Strictly the 4 Public Demo Personas)
# -----------------------------------------------------------------------------

@router.get("/users", response_model=List[AdminUserRead])
async def list_demo_users(
    admin_user: UserProfile = Depends(require_demo_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Lists only public demonstration users."""
    res = await db.execute(
        select(UserProfile).where(UserProfile.email.in_(DEMO_EMAILS))
    )
    users = res.scalars().all()
    return [
        AdminUserRead(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            account_type=u.account_type,
            is_platform_admin=u.is_platform_admin,
            is_active=u.is_active,
            vetting_status=getattr(u, "vetting_status", "approved"),
            created_at=u.created_at,
            organizations_count=1,
        )
        for u in users
    ]


# -----------------------------------------------------------------------------
# 4. Demo Agencies (Strictly Demo Agency Partner)
# -----------------------------------------------------------------------------

@router.get("/agencies")
async def list_demo_agencies(
    admin_user: UserProfile = Depends(require_demo_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Lists only the verified demonstration growth agency."""
    res = await db.execute(select(AgencyProfile).where(AgencyProfile.is_demo.is_(True)))
    agencies = res.scalars().all()
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "slug": a.slug,
            "city": a.city,
            "state": a.state,
            "verification_status": a.verification_status,
            "verification_notes": a.verification_notes or "Verified demo agency partner profile.",
            "is_available": a.is_available,
            "tier": a.tier,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in agencies
    ]


# -----------------------------------------------------------------------------
# 5. Demo Consultations & Support Activity
# -----------------------------------------------------------------------------

@router.get("/consultations")
async def list_demo_consultations(
    admin_user: UserProfile = Depends(require_demo_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Lists sample strategic advisory consultations."""
    res = await db.execute(select(ConsultationRequest).order_by(ConsultationRequest.created_at.desc()))
    consultations = res.scalars().all()
    return {
        "stats": {
            "total": len(consultations),
            "confirmed": sum(1 for c in consultations if c.status == "confirmed"),
            "completed": sum(1 for c in consultations if c.status == "completed"),
            "rescheduled": sum(1 for c in consultations if c.status == "rescheduled"),
        },
        "consultations": [
            {
                "id": str(c.id),
                "consultant_name": c.consultant_name,
                "client_name": c.client_name,
                "client_email": c.client_email,
                "scheduled_date": c.scheduled_date.isoformat() if c.scheduled_date else None,
                "slot_time": c.slot_time,
                "status": c.status,
                "topic": c.topic,
                "brand_website": c.brand_website,
            }
            for c in consultations
        ],
    }


# -----------------------------------------------------------------------------
# 6. Demo Service Orders
# -----------------------------------------------------------------------------

@router.get("/service-orders", response_model=List[ServiceOrderRead])
async def list_demo_service_orders(
    admin_user: UserProfile = Depends(require_demo_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Lists sample service engagements."""
    res = await db.execute(
        select(ServiceOrder)
        .options(selectinload(ServiceOrder.organization))
        .where(ServiceOrder.organization_id == DEMO_BRAND_ORG_ID)
    )
    orders = res.scalars().all()
    return [
        ServiceOrderRead(
            id=o.id,
            organization_id=o.organization_id,
            organization_name=o.organization.name if o.organization else "Aura Terra Living (Demo)",
            service_type=o.service_type,
            status=o.status,
            amount_inr=o.amount_inr,
            deliverables_url=o.deliverables_url,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )
        for o in orders
    ]


# -----------------------------------------------------------------------------
# 7. Demo Publishing Jobs
# -----------------------------------------------------------------------------

@router.get("/jobs", response_model=List[AdminJobRead])
async def list_demo_publishing_jobs(
    admin_user: UserProfile = Depends(require_demo_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Lists sample publishing and catalog synchronization jobs."""
    res = await db.execute(
        select(PublishingJob)
        .options(selectinload(PublishingJob.channel_connection))
        .where(PublishingJob.organization_id == DEMO_BRAND_ORG_ID)
        .limit(20)
    )
    jobs = res.scalars().all()
    return [
        AdminJobRead(
            id=j.id,
            organization_id=j.organization_id,
            organization_name="Aura Terra Living (Demo)",
            channel_type=j.channel_connection.channel_type if j.channel_connection else "shopify",
            job_type="product_sync",
            status=j.status,
            items_total=j.items_total or 18,
            items_succeeded=j.items_succeeded or 18,
            items_failed=j.items_failed or 0,
            retry_count=j.retry_count or 0,
            error_details=j.error_details,
            created_at=j.created_at,
            updated_at=j.updated_at,
        )
        for j in jobs
    ]


# -----------------------------------------------------------------------------
# 8. Demo Audit Logs
# -----------------------------------------------------------------------------

@router.get("/audit-logs")
async def list_demo_audit_logs(
    admin_user: UserProfile = Depends(require_demo_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Returns sample demonstration audit log events."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return [
        {
            "id": str(uuid.uuid4()),
            "timestamp": (now - datetime.timedelta(minutes=15)).isoformat(),
            "actor_email": "demo.admin@marketpath.ai",
            "action": "DEMO_EXPLORATION_SESSION_STARTED",
            "resource": "platform:demo-admin",
            "details": "Recruiter demo operator console opened. Read-only telemetry session initialized.",
            "ip_address": "127.0.0.1",
        },
        {
            "id": str(uuid.uuid4()),
            "timestamp": (now - datetime.timedelta(hours=2)).isoformat(),
            "actor_email": "demo.company@marketpath.ai",
            "action": "OMNICHANNEL_CATALOG_SYNC_COMPLETED",
            "resource": "channel:shopify",
            "details": "18 artisanal home living products synchronized with Shopify channel.",
            "ip_address": "127.0.0.1",
        },
        {
            "id": str(uuid.uuid4()),
            "timestamp": (now - datetime.timedelta(hours=5)).isoformat(),
            "actor_email": "demo.agency@marketpath.ai",
            "action": "SERVICE_PACKAGE_PUBLISHED",
            "resource": "agency:packages",
            "details": "Agency partner published 'D2C Omni Channel Launch Acceleration' package.",
            "ip_address": "127.0.0.1",
        },
        {
            "id": str(uuid.uuid4()),
            "timestamp": (now - datetime.timedelta(hours=12)).isoformat(),
            "actor_email": "demo.consultant@marketpath.ai",
            "action": "DIAGNOSTIC_NOTE_SAVED",
            "resource": "consultant:diagnostics",
            "details": "Confidential advisory assessment updated for Aura Terra Living.",
            "ip_address": "127.0.0.1",
        },
    ]


# -----------------------------------------------------------------------------
# 9. Plans and Connector Health
# -----------------------------------------------------------------------------

@router.get("/plans", response_model=List[PlanRead])
async def list_demo_plans(
    admin_user: UserProfile = Depends(require_demo_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Lists standard plans."""
    res = await db.execute(select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.price_inr.asc()))
    plans = res.scalars().all()
    return [PlanRead.model_validate(p) for p in plans]


@router.get("/integrations")
async def get_demo_integrations(
    admin_user: UserProfile = Depends(require_demo_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Returns sample demonstration connector cluster telemetry."""
    return {
        "shopify": {
            "status": "HEALTHY",
            "active_connections": 1,
            "rate_limit_usage": "3.8%",
            "environment": "Mock/Sandbox Demonstration",
        },
        "instagram": {
            "status": "HEALTHY",
            "active_connections": 1,
            "api_version": "v26.0",
            "environment": "Mock/Sandbox Demonstration",
        },
        "amazon": {
            "status": "CONFIGURED",
            "active_connections": 1,
            "environment": "SP-API Sandbox",
        },
        "flipkart": {
            "status": "CONFIGURED",
            "active_connections": 1,
            "environment": "Seller Hub Sandbox",
        },
    }


# -----------------------------------------------------------------------------
# 10. Mutation Rejection Guards (Strictly Read-Only Demo Environment)
# -----------------------------------------------------------------------------

@router.patch("/organizations/{organization_id}/status")
@router.post("/organizations/{organization_id}/suspend")
@router.post("/users/{user_id}/suspend")
@router.post("/users/{user_id}/reactivate")
@router.post("/users/{user_id}/revoke-sessions")
@router.patch("/users/{user_id}/admin-status")
@router.patch("/consultants/{user_id}/vetting")
@router.patch("/agencies/{agency_id}/verification")
@router.post("/plans")
@router.put("/plans/{plan_id}")
@router.post("/jobs/{job_id}/retry")
@router.put("/service-orders/{order_id}")
async def reject_demo_admin_mutations(
    admin_user: UserProfile = Depends(require_demo_admin_access),
):
    """Explicitly rejects any mutation attempted by the Demo Administrator persona."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Demonstration console is strictly read-only. Modifying system records or tenant configurations requires real Platform Administrator credentials.",
    )

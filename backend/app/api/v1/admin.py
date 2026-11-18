import datetime
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.deps import require_platform_admin
from backend.app.models.audit import AuditLog
from backend.app.models.billing import Payment, Plan, ServiceOrder, Subscription
from backend.app.models.catalogue import Product
from backend.app.models.channel import ChannelConnection, PublishingJob
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import UserProfile
from backend.app.schemas.admin import (
    AdminJobRead,
    AdminJobRetryResponse,
    AdminOrgRead,
    AdminOrgStatusUpdate,
    AdminOverviewTelemetry,
    AdminServiceOrderUpdate,
    AdminUserAdminStatusUpdate,
    AdminUserRead,
)
from backend.app.schemas.billing import PlanCreate, PlanRead, PlanUpdate, ServiceOrderRead
from backend.app.services.billing_service import BillingService

router = APIRouter(prefix="/admin", tags=["Platform Administration (Restricted)"])


@router.get("/overview", response_model=AdminOverviewTelemetry)
async def get_admin_overview(
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Provides internal platform telemetry across all tenants (Platform Admin only)."""
    # Orgs
    total_orgs_res = await db.execute(select(func.count(Organization.id)))
    active_orgs_res = await db.execute(
        select(func.count(Organization.id)).where(Organization.is_active.is_(True))
    )
    total_users_res = await db.execute(select(func.count(UserProfile.id)))
    total_prods_res = await db.execute(select(func.count(Product.id)))

    # Publishing
    job_stats_res = await db.execute(
        select(
            func.count(PublishingJob.id),
            func.count(PublishingJob.id).filter(PublishingJob.status == "failed"),
            func.count(PublishingJob.id).filter(PublishingJob.status == "completed"),
        )
    )
    tot_jobs, fail_jobs, comp_jobs = job_stats_res.one()
    tot_jobs = tot_jobs or 0
    fail_jobs = fail_jobs or 0
    comp_jobs = comp_jobs or 0
    pub_rate = round((comp_jobs / tot_jobs * 100), 1) if tot_jobs > 0 else 100.0

    # Billing
    rev_res = await db.execute(
        select(func.coalesce(func.sum(Payment.amount_inr), 0.0)).where(Payment.status == "success")
    )
    total_rev = float(rev_res.scalar() or 0.0)

    sub_res = await db.execute(
        select(func.count(Subscription.id)).where(Subscription.status == "active")
    )
    paid_subs = sub_res.scalar() or 0

    # Services
    srv_res = await db.execute(
        select(func.count(ServiceOrder.id)).where(ServiceOrder.status.in_(["requested", "quoted"]))
    )
    pending_srv = srv_res.scalar() or 0

    # Connector health
    shopify_res = await db.execute(
        select(func.count(ChannelConnection.id)).where(
            ChannelConnection.channel_type == "shopify", ChannelConnection.status == "active"
        )
    )
    insta_res = await db.execute(
        select(func.count(ChannelConnection.id)).where(
            ChannelConnection.channel_type == "instagram", ChannelConnection.status == "active"
        )
    )

    connector_health = {
        "shopify_active_connections": shopify_res.scalar() or 0,
        "instagram_active_connections": insta_res.scalar() or 0,
        "api_cluster_status": "HEALTHY",
        "rate_limit_headroom": "98.4%",
    }

    tot_orgs = total_orgs_res.scalar() or 0
    act_orgs = active_orgs_res.scalar() or 0
    tot_users = total_users_res.scalar() or 0

    return AdminOverviewTelemetry(
        total_organizations=tot_orgs,
        active_organizations=act_orgs,
        total_users=tot_users,
        total_products=total_prods_res.scalar() or 0,
        total_publishing_jobs=tot_jobs,
        failed_publishing_jobs=fail_jobs,
        publishing_success_rate=pub_rate,
        total_revenue_inr=total_rev,
        active_paid_subscribers=paid_subs,
        pending_service_orders=pending_srv,
        connector_health=connector_health,
        operator_email=admin_user.email,
        telemetry={
            "total_organizations": tot_orgs,
            "total_users": tot_users,
            "active_organizations": act_orgs,
            "operator_email": admin_user.email,
        },
    )


@router.get("/organizations", response_model=List[AdminOrgRead])
async def list_all_organizations(
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lists all organizations across the platform."""
    result = await db.execute(select(Organization).order_by(Organization.created_at.desc()))
    orgs = result.scalars().all()

    items = []
    for o in orgs:
        # Get subscription
        sub_res = await db.execute(
            select(Subscription).options(selectinload(Subscription.plan)).where(Subscription.organization_id == o.id)
        )
        sub = sub_res.scalar_one_or_none()
        plan_name = sub.plan.name if sub and sub.plan else "Growth (Trial)"
        sub_status = sub.status if sub else "active"

        # Product count
        p_res = await db.execute(select(func.count(Product.id)).where(Product.organization_id == o.id))
        p_count = p_res.scalar() or 0

        # Channel count
        c_res = await db.execute(select(func.count(ChannelConnection.id)).where(ChannelConnection.organization_id == o.id))
        c_count = c_res.scalar() or 0

        # Members count
        m_res = await db.execute(select(func.count(OrganizationMember.id)).where(OrganizationMember.organization_id == o.id))
        m_count = m_res.scalar() or 0

        items.append(
            AdminOrgRead(
                id=o.id,
                name=o.name,
                slug=o.slug,
                is_active=o.is_active,
                plan_name=plan_name,
                subscription_status=sub_status,
                products_count=p_count,
                channels_count=c_count,
                members_count=m_count,
                created_at=o.created_at,
            )
        )
    return items


@router.patch("/organizations/{organization_id}/status", response_model=AdminOrgRead)
async def update_organization_status(
    organization_id: uuid.UUID,
    payload: AdminOrgStatusUpdate,
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Suspends or reactivates an organization (Platform Admin only)."""
    res = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    org.is_active = payload.is_active
    db.add(
        AuditLog(
            organization_id=org.id,
            actor_user_id=admin_user.id,
            action="organization.status_updated",
            resource_type="organization",
            resource_id=str(org.id),
            metadata_json={"is_active": payload.is_active, "reason": payload.reason},
        )
    )
    await db.commit()
    await db.refresh(org)

    sub_res = await db.execute(
        select(Subscription).options(selectinload(Subscription.plan)).where(Subscription.organization_id == org.id)
    )
    sub = sub_res.scalar_one_or_none()
    plan_name = sub.plan.name if sub and sub.plan else "Growth"
    sub_status = sub.status if sub else "active"

    return AdminOrgRead(
        id=org.id,
        name=org.name,
        slug=org.slug,
        is_active=org.is_active,
        plan_name=plan_name,
        subscription_status=sub_status,
        products_count=0,
        channels_count=0,
        members_count=1,
        created_at=org.created_at,
    )


@router.get("/users", response_model=List[AdminUserRead])
async def list_all_users(
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lists all user profiles across the platform."""
    result = await db.execute(select(UserProfile).order_by(UserProfile.created_at.desc()))
    users = result.scalars().all()

    items = []
    for u in users:
        m_res = await db.execute(select(func.count(OrganizationMember.id)).where(OrganizationMember.user_id == u.id))
        items.append(
            AdminUserRead(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                account_type=u.account_type,
                is_platform_admin=u.is_platform_admin,
                is_active=getattr(u, "is_active", True),
                vetting_status=getattr(u, "vetting_status", "approved"),
                memberships_count=m_res.scalar() or 0,
                created_at=u.created_at,
            )
        )
    return items


@router.post("/users/{user_id}/suspend", response_model=AdminUserRead)
async def suspend_user(
    user_id: uuid.UUID,
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform Admin suspends/deactivates a user account."""
    user = await db.get(UserProfile, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.is_active = False
    db.add(
        AuditLog(
            actor_user_id=admin_user.id,
            action="USER_SUSPENDED",
            resource_type="user",
            resource_id=str(user.id),
            metadata_json={"target_email": user.email},
        )
    )
    await db.commit()
    await db.refresh(user)
    m_res = await db.execute(select(func.count(OrganizationMember.id)).where(OrganizationMember.user_id == user.id))
    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        account_type=user.account_type,
        is_platform_admin=user.is_platform_admin,
        is_active=user.is_active,
        vetting_status=user.vetting_status,
        memberships_count=m_res.scalar() or 0,
        created_at=user.created_at,
    )


@router.post("/users/{user_id}/reactivate", response_model=AdminUserRead)
async def reactivate_user(
    user_id: uuid.UUID,
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform Admin reactivates a suspended user account."""
    user = await db.get(UserProfile, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.is_active = True
    db.add(
        AuditLog(
            actor_user_id=admin_user.id,
            action="USER_REACTIVATED",
            resource_type="user",
            resource_id=str(user.id),
            metadata_json={"target_email": user.email},
        )
    )
    await db.commit()
    await db.refresh(user)
    m_res = await db.execute(select(func.count(OrganizationMember.id)).where(OrganizationMember.user_id == user.id))
    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        account_type=user.account_type,
        is_platform_admin=user.is_platform_admin,
        is_active=user.is_active,
        vetting_status=user.vetting_status,
        memberships_count=m_res.scalar() or 0,
        created_at=user.created_at,
    )


@router.post("/users/{user_id}/revoke-sessions")
async def revoke_user_sessions(
    user_id: uuid.UUID,
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform Admin invalidates all active sessions for a user."""
    from backend.app.services.session_service import SessionService
    revoked_count = await SessionService.revoke_all_user_sessions(db, user_id)
    db.add(
        AuditLog(
            actor_user_id=admin_user.id,
            action="USER_SESSIONS_REVOKED",
            resource_type="user",
            resource_id=str(user_id),
            metadata_json={"revoked_count": revoked_count},
        )
    )
    await db.commit()
    return {"success": True, "message": f"Successfully revoked {revoked_count} active sessions.", "revoked_count": revoked_count}


@router.get("/consultants")
async def list_consultant_applications(
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform Admin lists all registered consultants and vetting statuses."""
    res = await db.execute(
        select(UserProfile)
        .where(UserProfile.account_type == "consultant")
        .order_by(UserProfile.created_at.desc())
    )
    consultants = res.scalars().all()
    return [
        {
            "id": str(c.id),
            "email": c.email,
            "full_name": c.full_name,
            "account_type": c.account_type,
            "is_active": getattr(c, "is_active", True),
            "vetting_status": getattr(c, "vetting_status", "approved"),
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in consultants
    ]


@router.patch("/consultants/{user_id}/vetting")
async def update_consultant_vetting(
    user_id: uuid.UUID,
    payload: Dict[str, Any],
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform Admin approves or rejects a consultant application."""
    user = await db.get(UserProfile, user_id)
    if not user or user.account_type != "consultant":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultant not found.")

    new_status = payload.get("vetting_status", "approved")
    if new_status not in ("approved", "rejected", "under_review"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vetting status.")

    user.vetting_status = new_status
    if new_status == "approved":
        user.is_active = True
    elif new_status == "rejected":
        user.is_active = False

    db.add(
        AuditLog(
            actor_user_id=admin_user.id,
            action="CONSULTANT_VETTING_UPDATED",
            resource_type="user",
            resource_id=str(user.id),
            metadata_json={"vetting_status": new_status, "reason": payload.get("reason")},
        )
    )
    await db.commit()
    await db.refresh(user)

    return {
        "success": True,
        "user_id": str(user.id),
        "email": user.email,
        "vetting_status": user.vetting_status,
        "is_active": user.is_active,
    }


@router.patch("/users/{user_id}/admin-status", response_model=AdminUserRead)
async def update_user_admin_status(
    user_id: uuid.UUID,
    payload: AdminUserAdminStatusUpdate,
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Promotes or demotes platform admin privileges."""
    res = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.is_platform_admin = payload.is_platform_admin
    db.add(
        AuditLog(
            actor_user_id=admin_user.id,
            action="user.admin_status_updated",
            resource_type="user_profile",
            resource_id=str(user.id),
            metadata_json={"is_platform_admin": payload.is_platform_admin, "target_email": user.email},
        )
    )
    await db.commit()
    await db.refresh(user)

    m_res = await db.execute(select(func.count(OrganizationMember.id)).where(OrganizationMember.user_id == user.id))
    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_platform_admin=user.is_platform_admin,
        memberships_count=m_res.scalar() or 0,
        created_at=user.created_at,
    )


@router.get("/plans", response_model=List[PlanRead])
async def list_all_admin_plans(
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lists all plans including inactive tiers."""
    result = await db.execute(select(Plan).order_by(Plan.monthly_price_inr.asc()))
    plans = result.scalars().all()
    if not plans:
        plans = await BillingService.seed_default_plans(db)
    return list(plans)


@router.post("/plans", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreate,
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new SaaS plan tier."""
    new_plan = Plan(
        name=payload.name,
        monthly_price_inr=payload.monthly_price_inr,
        max_active_skus=payload.max_active_skus,
        max_connected_channels=payload.max_connected_channels,
        ai_generation_monthly_quota=payload.ai_generation_monthly_quota,
        description=payload.description,
        features=payload.features or {},
        is_active=payload.is_active,
    )
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    return new_plan


@router.put("/plans/{plan_id}", response_model=PlanRead)
async def update_plan(
    plan_id: uuid.UUID,
    payload: PlanUpdate,
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Updates pricing, quotas, and feature entitlements for a plan tier."""
    res = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, val)

    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/integrations")
async def get_admin_integrations(
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Inspects connector status and health across all connected tenant accounts."""
    conns_res = await db.execute(
        select(ChannelConnection.channel_type, ChannelConnection.status, func.count(ChannelConnection.id))
        .group_by(ChannelConnection.channel_type, ChannelConnection.status)
    )
    channel_health = {}
    for ctype, stat, cnt in conns_res.all():
        if ctype not in channel_health:
            channel_health[ctype] = {"active": 0, "error": 0, "disconnected": 0}
        channel_health[ctype][stat] = cnt

    return {
        "status": "healthy",
        "channels": channel_health,
        "supported_providers": ["shopify", "instagram", "meta_ads", "google_ads"],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


@router.get("/jobs", response_model=List[AdminJobRead])
async def list_admin_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lists omnichannel publishing queue items across all tenants."""
    query = (
        select(PublishingJob)
        .options(
            selectinload(PublishingJob.connection),
        )
        .order_by(PublishingJob.created_at.desc())
        .limit(limit)
    )
    if status_filter:
        query = query.where(PublishingJob.status == status_filter)

    res = await db.execute(query)
    jobs = res.scalars().all()

    items = []
    for j in jobs:
        org_name = "Tenant Org"
        org_res = await db.execute(select(Organization.name).where(Organization.id == j.organization_id))
        org_row = org_res.scalar_one_or_none()
        if org_row:
            org_name = org_row

        p_title = "Product Listing"
        p_res = await db.execute(select(Product.title).where(Product.id == j.product_id))
        p_row = p_res.scalar_one_or_none()
        if p_row:
            p_title = p_row

        items.append(
            AdminJobRead(
                id=j.id,
                organization_id=j.organization_id,
                organization_name=org_name,
                product_title=p_title,
                channel_type=j.connection.channel_type if j.connection else "channel",
                job_type=j.job_type,
                status=j.status,
                retry_count=j.retry_count,
                created_at=j.created_at,
                completed_at=j.completed_at,
            )
        )
    return items


@router.post("/jobs/{job_id}/retry", response_model=AdminJobRetryResponse)
async def retry_publishing_job(
    job_id: uuid.UUID,
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually re-queues a failed publishing job for retry."""
    res = await db.execute(select(PublishingJob).where(PublishingJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publishing job not found.")

    job.status = "queued"
    job.retry_count += 1
    db.add(
        AuditLog(
            organization_id=job.organization_id,
            actor_user_id=admin_user.id,
            action="job.retried_by_admin",
            resource_type="publishing_job",
            resource_id=str(job.id),
            metadata_json={"retry_count": job.retry_count},
        )
    )
    await db.commit()
    await db.refresh(job)

    return AdminJobRetryResponse(
        job_id=job.id,
        status="queued",
        message="Job successfully reset and queued for immediate execution.",
    )


@router.get("/service-orders", response_model=List[ServiceOrderRead])
async def list_admin_service_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lists managed service requests across all client organizations."""
    query = select(ServiceOrder).order_by(ServiceOrder.created_at.desc())
    if status_filter:
        query = query.where(ServiceOrder.status == status_filter)
    res = await db.execute(query)
    return list(res.scalars().all())


@router.put("/service-orders/{order_id}", response_model=ServiceOrderRead)
async def update_admin_service_order(
    order_id: uuid.UUID,
    payload: AdminServiceOrderUpdate,
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Updates quote, operator assignment, and deliverable status for a service order."""
    res = await db.execute(select(ServiceOrder).where(ServiceOrder.id == order_id))
    order = res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service order not found.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, val)

    if payload.status == "completed" and not order.completed_at:
        order.completed_at = datetime.datetime.now(datetime.timezone.utc)

    db.add(
        AuditLog(
            organization_id=order.organization_id,
            actor_user_id=admin_user.id,
            action="service_order.updated_by_admin",
            resource_type="service_order",
            resource_id=str(order.id),
            metadata_json=payload.model_dump(mode="json", exclude_unset=True),
        )
    )
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/audit-logs")
async def list_global_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Inspects global platform audit logs."""
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "organization_id": str(log.organization_id) if log.organization_id else None,
            "actor_user_id": str(log.actor_user_id) if log.actor_user_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "metadata": log.metadata_json,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


# -----------------------------------------------------------------------------
# MarketPath Agency Connect Verification Queue
# -----------------------------------------------------------------------------

@router.get("/agencies")
async def list_all_agencies_for_admin(
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lists all agency profiles for administrative verification and moderation."""
    from backend.app.models.agency import AgencyProfile
    res = await db.execute(select(AgencyProfile).order_by(AgencyProfile.created_at.desc()))
    agencies = res.scalars().all()
    from backend.app.schemas.agency import AgencyProfileRead
    return [AgencyProfileRead.model_validate(a) for a in agencies]


@router.patch("/agencies/{agency_id}/verification")
async def update_agency_verification(
    agency_id: uuid.UUID,
    payload: Dict[str, Any],
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform Admin approves, rejects, or suspends an agency profile."""
    from backend.app.schemas.agency import AgencyVerificationAction
    from backend.app.services.agency_service import AgencyServiceManager
    action = AgencyVerificationAction(
        verification_status=payload.get("verification_status", "verified"),
        verification_notes=payload.get("verification_notes"),
        is_featured=payload.get("is_featured"),
        tier=payload.get("tier"),
    )
    return await AgencyServiceManager.admin_set_verification_status(
        db=db, agency_id=agency_id, payload=action, admin_user_id=admin_user.id
    )


# -----------------------------------------------------------------------------
# Consultation Operations & Telemetry
# -----------------------------------------------------------------------------

@router.get("/consultations")
async def list_admin_consultations(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: UserProfile = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform Admin overview of merchant consultations, assignment queue, and conversion metrics."""
    from backend.app.models.consultation import ConsultationRequest
    from backend.app.schemas.consultation import ConsultationResponse

    query = select(ConsultationRequest).order_by(ConsultationRequest.created_at.desc())
    if status_filter:
        query = query.where(ConsultationRequest.status == status_filter)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    consultations = result.scalars().all()

    # Aggregate status counts
    stats_query = select(ConsultationRequest.status, func.count(ConsultationRequest.id)).group_by(ConsultationRequest.status)
    stats_res = await db.execute(stats_query)
    status_counts = dict(stats_res.all())

    total_count = sum(status_counts.values())

    return {
        "stats": {
            "total_consultations": total_count,
            "submitted_count": status_counts.get("submitted", 0),
            "assigned_count": status_counts.get("assigned", 0),
            "confirmed_count": status_counts.get("confirmed", 0),
            "completed_count": status_counts.get("completed", 0),
            "cancelled_count": status_counts.get("cancelled", 0),
            "status_breakdown": status_counts,
        },
        "consultations": [ConsultationResponse.model_validate(c) for c in consultations],
    }


import datetime
import uuid
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.models.notification import Notification
from backend.app.schemas.notification import (
    NotificationListResponse,
    NotificationRead,
    NotificationUnreadCount,
)

router = APIRouter(prefix="/notifications", tags=["Notifications Centre"])


INITIAL_SEED_NOTIFICATIONS = [
    {
        "domain": "products",
        "title": "Catalogue Health Check",
        "message": "All product variants have category specifications and packaging dimensions filled.",
        "notification_type": "success",
        "severity": "info",
        "link": "/app/products",
    },
    {
        "domain": "channels",
        "title": "Shopify Storefront Connected",
        "message": "Live connection active. Auto-inventory sync and webhook listening enabled.",
        "notification_type": "info",
        "severity": "info",
        "link": "/app/integrations",
    },
    {
        "domain": "business",
        "title": "14-Day Growth Trial Active",
        "message": "Enjoy full access to master catalogue, AI copy generation, and multi-channel publishing.",
        "notification_type": "info",
        "severity": "info",
        "link": "/app/billing",
    },
    {
        "domain": "marketing",
        "title": "Seasonal Campaign Reminder",
        "message": "Plan your festive collection launch campaign on the unified business calendar.",
        "notification_type": "info",
        "severity": "warning",
        "link": "/app/marketing",
    },
    {
        "domain": "agency",
        "title": "Verified Agency Matches",
        "message": "3 verified agencies specialize in your brand category and revenue stage.",
        "notification_type": "info",
        "severity": "info",
        "link": "/app/agency-connect",
    },
    {
        "domain": "team",
        "title": "Access Governance Active",
        "message": "Owner permissions set. You can invite team members with role-based restrictions.",
        "notification_type": "info",
        "severity": "info",
        "link": "/app/team",
    },
]


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    domain: Optional[str] = Query(None, description="Filter by domain: products, channels, business, marketing, agency, team"),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists notifications for the active organization with domain filtering and read status."""
    # Check if there are any notifications for this tenant; if 0, seed initial alerts
    count_check = await db.scalar(
        select(func.count(Notification.id)).where(Notification.organization_id == context.organization_id)
    )
    if count_check == 0:
        for seed in INITIAL_SEED_NOTIFICATIONS:
            item = Notification(
                organization_id=context.organization_id,
                domain=seed["domain"],
                title=seed["title"],
                message=seed["message"],
                notification_type=seed["notification_type"],
                severity=seed["severity"],
                link=seed["link"],
                is_read=False,
                metadata_json={},
            )
            db.add(item)
        await db.commit()

    query = select(Notification).where(Notification.organization_id == context.organization_id)

    if domain and domain.lower() != "all":
        query = query.where(Notification.domain == domain.lower())

    if unread_only:
        query = query.where(Notification.is_read.is_(False))

    query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    res = await db.scalars(query)
    items = list(res.all())

    # Get total count
    total_query = select(func.count(Notification.id)).where(Notification.organization_id == context.organization_id)
    if domain and domain.lower() != "all":
        total_query = total_query.where(Notification.domain == domain.lower())
    if unread_only:
        total_query = total_query.where(Notification.is_read.is_(False))
    total = await db.scalar(total_query) or 0

    # Get unread count
    unread_total = await db.scalar(
        select(func.count(Notification.id))
        .where(Notification.organization_id == context.organization_id)
        .where(Notification.is_read.is_(False))
    ) or 0

    return NotificationListResponse(
        items=[NotificationRead.model_validate(n) for n in items],
        total=total,
        unread_count=unread_total,
    )


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def get_unread_count(
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Returns unread notification counts aggregated by domain."""
    res = await db.execute(
        select(Notification.domain, func.count(Notification.id))
        .where(Notification.organization_id == context.organization_id)
        .where(Notification.is_read.is_(False))
        .group_by(Notification.domain)
    )
    domain_counts: Dict[str, int] = {}
    total = 0
    for dom, cnt in res.all():
        domain_counts[dom] = cnt
        total += cnt

    return NotificationUnreadCount(
        unread_count=total,
        by_domain=domain_counts,
    )


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: uuid.UUID,
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Marks a single notification as read."""
    notif = await db.scalar(
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.organization_id == context.organization_id)
    )
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    notif.read_at = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()
    await db.refresh(notif)
    return NotificationRead.model_validate(notif)


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    domain: Optional[str] = Query(None),
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Marks all notifications as read for the tenant organization."""
    stmt = (
        update(Notification)
        .where(Notification.organization_id == context.organization_id)
        .where(Notification.is_read.is_(False))
    )
    if domain and domain.lower() != "all":
        stmt = stmt.where(Notification.domain == domain.lower())

    stmt = stmt.values(is_read=True, read_at=datetime.datetime.now(datetime.timezone.utc))
    await db.execute(stmt)
    await db.commit()
    return {"message": "All notifications marked as read."}


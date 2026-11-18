import re
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, get_current_tenant_context, get_current_user, require_role
from backend.app.models.audit import AuditLog
from backend.app.models.brand import BrandProfile
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import UserProfile
from backend.app.schemas.organization import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
    OrganizationWithRole,
)

router = APIRouter(prefix="/organizations", tags=["Organizations & Tenancy"])


def _generate_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        slug = f"org-{uuid.uuid4().hex[:6]}"
    return slug


@router.get("", response_model=List[OrganizationWithRole])
async def list_user_organizations(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all organizations the authenticated user belongs to."""
    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.organization))
        .where(OrganizationMember.user_id == current_user.id)
    )
    memberships = result.scalars().all()

    return [
        OrganizationWithRole(
            id=m.organization.id,
            name=m.organization.name,
            slug=m.organization.slug,
            is_active=m.organization.is_active,
            settings=m.organization.settings,
            created_at=m.organization.created_at,
            updated_at=m.organization.updated_at,
            role=m.role,
        )
        for m in memberships
        if m.organization and m.organization.is_active
    ]


@router.post("", response_model=OrganizationWithRole, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new organization during seller onboarding, establishes owner role, and initializes brand profile."""
    # Determine unique slug
    base_slug = payload.slug or _generate_slug(payload.name)
    slug = base_slug
    attempt = 1
    while True:
        existing = await db.execute(select(Organization).where(Organization.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{attempt}"
        attempt += 1

    org = Organization(
        name=payload.name,
        slug=slug,
        is_active=True,
        settings={
            "currency": payload.currency or "INR",
            "timezone": payload.timezone or "Asia/Kolkata",
            "category": payload.category or "Home & Living",
        },
    )
    db.add(org)
    await db.flush()

    # Add creator as 'owner'
    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(member)

    # Initialize initial Brand Profile
    brand_name = payload.brand_name or payload.name
    brand = BrandProfile(
        organization_id=org.id,
        brand_name=brand_name,
        tagline=f"Premium Handcrafted {payload.category or 'Home & Living'} from India",
        story=f"{brand_name} is dedicated to bringing authentic, sustainable, and design-led products to modern homes.",
        tone_of_voice="Warm & Aesthetic",
        archetype="Creator & Explorer",
        target_audience_summary="Urban Indian households, design-conscious professionals, and thoughtful gifting shoppers.",
    )
    db.add(brand)

    # Record Audit Log
    audit = AuditLog(
        organization_id=org.id,
        actor_user_id=current_user.id,
        action="ORGANIZATION_CREATED",
        resource_type="organization",
        resource_id=str(org.id),
        metadata_json={"org_name": org.name, "slug": org.slug},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(org)

    return OrganizationWithRole(
        id=org.id,
        name=org.name,
        slug=org.slug,
        is_active=org.is_active,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
        role="owner",
    )


@router.get("/active", response_model=OrganizationWithRole)
async def get_active_organization(
    context: TenantContext = Depends(require_role(["viewer"])),
):
    """Retrieves the active organization details based on the X-Organization-Id header."""
    org = context.organization
    return OrganizationWithRole(
        id=org.id,
        name=org.name,
        slug=org.slug,
        is_active=org.is_active,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
        role=context.role,
    )


@router.patch("/active", response_model=OrganizationRead)
async def update_active_organization(
    payload: OrganizationUpdate,
    context: TenantContext = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db),
):
    """Updates active organization settings (requires admin or owner role)."""
    org = context.organization
    if payload.name is not None:
        org.name = payload.name
    if payload.settings is not None:
        merged_settings = dict(org.settings)
        merged_settings.update(payload.settings)
        org.settings = merged_settings

    audit = AuditLog(
        organization_id=org.id,
        actor_user_id=context.user.id,
        action="ORGANIZATION_UPDATED",
        resource_type="organization",
        resource_id=str(org.id),
        metadata_json={"updated_fields": list(payload.model_dump(exclude_unset=True).keys())},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(org)
    return OrganizationRead.model_validate(org)


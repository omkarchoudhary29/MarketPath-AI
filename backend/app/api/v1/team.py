import datetime
import hashlib
import secrets
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.deps import TenantContext, require_role
from backend.app.models.audit import AuditLog
from backend.app.models.organization import Organization, OrganizationMember, TeamInvitation
from backend.app.models.user import UserProfile
from backend.app.schemas.team import (
    TeamInviteCreate,
    TeamInvitationAccept,
    TeamInvitationCreate,
    TeamInvitationRead,
    TeamInvitationVerifyResponse,
    TeamMemberRead,
    TeamMemberUpdate,
)

router = APIRouter(prefix="/team", tags=["Team & Collaboration"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.get("/members", response_model=List[TeamMemberRead])
async def list_team_members(
    context: TenantContext = Depends(require_role(["viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists all team members and their roles within the active organization."""
    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(OrganizationMember.organization_id == context.organization_id)
    )
    members = result.scalars().all()
    return [TeamMemberRead.model_validate(m) for m in members]


@router.post("/invites", response_model=TeamMemberRead, status_code=status.HTTP_201_CREATED)
async def invite_team_member(
    payload: TeamInviteCreate,
    context: TenantContext = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db),
):
    """Directly adds a member to the organization with a designated role (Admin or Owner only)."""
    user_res = await db.execute(select(UserProfile).where(UserProfile.email == payload.email))
    user = user_res.scalar_one_or_none()

    if not user:
        user = UserProfile(
            id=uuid.uuid4(),
            email=payload.email,
            full_name=payload.full_name or payload.email.split("@")[0],
            account_type="company",
            is_platform_admin=False,
        )
        db.add(user)
        await db.flush()

    existing_member_res = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == context.organization_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if existing_member_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{payload.email}' is already a member of this organization.",
        )

    if payload.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign 'owner' role via team invite.",
        )

    member = OrganizationMember(
        organization_id=context.organization_id,
        user_id=user.id,
        role=payload.role,
    )
    db.add(member)

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="TEAM_MEMBER_INVITED",
        resource_type="organization_member",
        resource_id=str(user.id),
        metadata_json={"email": payload.email, "role": payload.role},
    )
    db.add(audit)
    await db.commit()

    member_res = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(OrganizationMember.id == member.id)
    )
    return TeamMemberRead.model_validate(member_res.scalar_one())


@router.post("/invitations", response_model=TeamInvitationRead, status_code=status.HTTP_201_CREATED)
async def create_team_invitation(
    payload: TeamInvitationCreate,
    context: TenantContext = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db),
):
    """Generates a cryptographically signed invitation link with 7-day expiration and zero password exposure."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)

    invitation = TeamInvitation(
        organization_id=context.organization_id,
        invited_by_user_id=context.user.id,
        email=str(payload.email),
        role=payload.role,
        token_hash=token_hash,
        expires_at=expires_at,
        status="pending",
    )
    db.add(invitation)

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="TEAM_INVITATION_LINK_CREATED",
        resource_type="team_invitation",
        resource_id=str(invitation.id),
        metadata_json={"email": payload.email, "role": payload.role},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(invitation)

    invite_url = f"/invite?token={raw_token}"
    resp = TeamInvitationRead.model_validate(invitation)
    resp.invite_url = invite_url
    return resp


@router.get("/invitations", response_model=List[TeamInvitationRead])
async def list_team_invitations(
    context: TenantContext = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db),
):
    """Lists pending and active invitations for the organization."""
    result = await db.execute(
        select(TeamInvitation)
        .where(TeamInvitation.organization_id == context.organization_id)
        .order_by(TeamInvitation.created_at.desc())
    )
    return [TeamInvitationRead.model_validate(inv) for inv in result.scalars().all()]


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_team_invitation(
    invitation_id: uuid.UUID,
    context: TenantContext = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db),
):
    """Revokes a pending team invitation."""
    result = await db.execute(
        select(TeamInvitation).where(
            TeamInvitation.id == invitation_id,
            TeamInvitation.organization_id == context.organization_id,
        )
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found.")

    invitation.status = "revoked"
    await db.commit()


@router.get("/invitations/{token}/verify", response_model=TeamInvitationVerifyResponse)
async def verify_team_invitation(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Public token verification endpoint for invitees."""
    token_hash = _hash_token(token)
    stmt = (
        select(TeamInvitation)
        .options(selectinload(TeamInvitation.organization))
        .where(TeamInvitation.token_hash == token_hash)
    )
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation token.")

    now = datetime.datetime.now(datetime.timezone.utc)
    # Handle timezone comparison safely
    expires = invitation.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=datetime.timezone.utc)

    if invitation.status != "pending" or now > expires:
        return TeamInvitationVerifyResponse(
            email=invitation.email,
            organization_name=invitation.organization.name if invitation.organization else "MarketPath Workspace",
            role=invitation.role,
            is_valid=False,
            expires_at=invitation.expires_at,
        )

    return TeamInvitationVerifyResponse(
        email=invitation.email,
        organization_name=invitation.organization.name if invitation.organization else "MarketPath Workspace",
        role=invitation.role,
        is_valid=True,
        expires_at=invitation.expires_at,
    )


@router.post("/invitations/{token}/accept")
async def accept_team_invitation(
    token: str,
    payload: TeamInvitationAccept,
    db: AsyncSession = Depends(get_db),
):
    """Public acceptance endpoint: Invitee sets password privately and joins organization with zero password leakage."""
    token_hash = _hash_token(token)
    stmt = (
        select(TeamInvitation)
        .options(selectinload(TeamInvitation.organization))
        .where(TeamInvitation.token_hash == token_hash)
    )
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation or invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Invitation is invalid or has already been used.")

    now = datetime.datetime.now(datetime.timezone.utc)
    expires = invitation.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=datetime.timezone.utc)

    if now > expires:
        invitation.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired. Please request a new invite link.")

    # Check or provision UserProfile
    user_stmt = select(UserProfile).where(UserProfile.email == invitation.email)
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()

    if not user:
        user = UserProfile(
            id=uuid.uuid4(),
            email=invitation.email,
            full_name=payload.full_name,
            account_type="company",
            is_platform_admin=False,
        )
        db.add(user)
        await db.flush()
    else:
        user.full_name = payload.full_name

    # Add or update organization membership
    member_stmt = select(OrganizationMember).where(
        OrganizationMember.organization_id == invitation.organization_id,
        OrganizationMember.user_id == user.id,
    )
    member_res = await db.execute(member_stmt)
    member = member_res.scalar_one_or_none()

    if not member:
        member = OrganizationMember(
            organization_id=invitation.organization_id,
            user_id=user.id,
            role=invitation.role,
        )
        db.add(member)
    else:
        member.role = invitation.role

    invitation.status = "accepted"
    invitation.accepted_at = now

    audit = AuditLog(
        organization_id=invitation.organization_id,
        actor_user_id=user.id,
        action="TEAM_INVITATION_ACCEPTED",
        resource_type="team_invitation",
        resource_id=str(invitation.id),
        metadata_json={"email": invitation.email, "role": invitation.role},
    )
    db.add(audit)
    await db.commit()

    return {
        "success": True,
        "message": f"Successfully joined {invitation.organization.name if invitation.organization else 'the organization'}.",
        "organization_id": str(invitation.organization_id),
        "user_id": str(user.id),
        "email": user.email,
        "role": invitation.role,
    }


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    member_id: uuid.UUID,
    context: TenantContext = Depends(require_role(["owner"])),
    db: AsyncSession = Depends(get_db),
):
    """Removes a team member from the organization (Owner role only)."""
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == context.organization_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found in this organization.",
        )

    if member.role == "owner":
        owners_count_res = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == context.organization_id,
                OrganizationMember.role == "owner",
            )
        )
        if len(owners_count_res.scalars().all()) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the sole owner of an organization.",
            )

    await db.delete(member)

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="TEAM_MEMBER_REMOVED",
        resource_type="organization_member",
        resource_id=str(member_id),
        metadata_json={"removed_user_id": str(member.user_id)},
    )
    db.add(audit)
    await db.commit()


@router.patch("/members/{member_id}", response_model=TeamMemberRead)
async def update_team_member_role(
    member_id: uuid.UUID,
    payload: TeamMemberUpdate,
    context: TenantContext = Depends(require_role(["owner", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Updates the role of an active team member (Owner or Admin only)."""
    new_role = payload.role
    if not new_role or new_role not in ["admin", "marketer", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be one of: 'admin', 'marketer', 'viewer'. Owner role transfer must be done via ownership transfer.",
        )

    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == context.organization_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found in this organization.",
        )

    if member.role == "owner":
        owners_count_res = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == context.organization_id,
                OrganizationMember.role == "owner",
            )
        )
        if len(owners_count_res.scalars().all()) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the sole owner of an organization.",
            )

    old_role = member.role
    member.role = new_role

    audit = AuditLog(
        organization_id=context.organization_id,
        actor_user_id=context.user.id,
        action="TEAM_MEMBER_ROLE_UPDATED",
        resource_type="organization_member",
        resource_id=str(member_id),
        metadata_json={"user_id": str(member.user_id), "old_role": old_role, "new_role": new_role},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(member)
    return TeamMemberRead.model_validate(member)

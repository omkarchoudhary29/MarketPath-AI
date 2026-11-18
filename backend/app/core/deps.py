import uuid
from dataclasses import dataclass
from typing import List, Optional
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import verify_jwt_token
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import UserProfile
from backend.app.services.session_service import SessionService

security_bearer = HTTPBearer(auto_error=False)

# Role hierarchy definition: higher roles inherit lower role permissions
ROLE_HIERARCHY = {
    "owner": ["owner", "admin", "marketer", "viewer"],
    "admin": ["admin", "marketer", "viewer"],
    "marketer": ["marketer", "viewer"],
    "viewer": ["viewer"],
}


@dataclass
class TenantContext:
    organization_id: uuid.UUID
    user: UserProfile
    role: str
    organization: Organization


async def get_current_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """Extracts, validates session token or JWT claims, and returns the authenticated UserProfile."""
    raw_token = None
    if auth and auth.credentials:
        raw_token = auth.credentials.strip()
    elif request.cookies.get("marketpath_session"):
        raw_token = request.cookies.get("marketpath_session", "").strip()

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header, Bearer token, or session cookie.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Primary: Validate against active database user_sessions
    db_session = await SessionService.get_session_by_token(db, raw_token)
    if db_session and db_session.user:
        return db_session.user

    # 2. Secondary: Fallback to cryptographically signed JWT for test/dev tokens
    try:
        claims = verify_jwt_token(raw_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or been revoked. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = claims.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject (sub) claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(str(sub))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Subject claim is not a valid UUID.",
        )

    # Query existing profile in database
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_uuid))
    user_profile = result.scalar_one_or_none()

    if not user_profile:
        # Auto-provision profile from claims during first authenticated request
        email = claims.get("email", f"{user_uuid}@example.com")
        user_metadata = claims.get("user_metadata", {})
        full_name = user_metadata.get("full_name") or claims.get("name") or email.split("@")[0]
        avatar_url = user_metadata.get("avatar_url")
        is_platform_admin = bool(claims.get("is_platform_admin", False))
        account_type = user_metadata.get("account_type", "company")

        user_profile = UserProfile(
            id=user_uuid,
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
            account_type=account_type,
            is_platform_admin=is_platform_admin,
        )
        db.add(user_profile)
        await db.commit()
        await db.refresh(user_profile)

    return user_profile


async def get_current_tenant_context(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantContext:
    """Verifies that the authenticated user is an active member of the requested organization."""
    if not x_organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required 'X-Organization-Id' header.",
        )

    try:
        org_uuid = uuid.UUID(x_organization_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 'X-Organization-Id' format. Must be a valid UUID.",
        )

    # Verify organization exists and is active
    org_res = await db.execute(
        select(Organization).where(Organization.id == org_uuid, Organization.is_active.is_(True))
    )
    organization = org_res.scalar_one_or_none()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or inactive.",
        )

    # Verify user's membership and retrieve role
    member_res = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_uuid,
            OrganizationMember.user_id == current_user.id,
        )
    )
    membership = member_res.scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this organization.",
        )

    return TenantContext(
        organization_id=org_uuid,
        user=current_user,
        role=membership.role,
        organization=organization,
    )


def require_role(allowed_roles: List[str]):
    """Enforces minimum RBAC role requirements within the active tenant organization."""

    async def role_checker(context: TenantContext = Depends(get_current_tenant_context)) -> TenantContext:
        user_role = context.role
        user_capabilities = ROLE_HIERARCHY.get(user_role, [])
        # Check if any of the user's role capabilities match the required allowed roles
        has_permission = any(role in user_capabilities for role in allowed_roles)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role in {allowed_roles}, your role is '{user_role}'.",
            )
        return context

    return role_checker


async def require_platform_admin(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """Enforces that the authenticated user has internal platform administrator privileges."""
    if not current_user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Platform Administrator privileges required.",
        )
    return current_user


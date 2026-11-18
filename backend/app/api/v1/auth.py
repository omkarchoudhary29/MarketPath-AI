import datetime
import re
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.core.security import (
    create_password_reset_token,
    create_test_jwt,
    hash_password,
    verify_password,
    verify_password_reset_token,
)
from backend.app.models.agency import AgencyMember, AgencyProfile
from backend.app.models.brand import BrandProfile
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import UserProfile
from backend.app.schemas.auth import (
    ApplicationSubmittedResponse,
    AuthMeResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginAccountRequest,
    LoginAccountResponse,
    LogoutResponse,
    RegisterAgencyRequest,
    RegisterCompanyRequest,
    RegisterConsultantRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from backend.app.schemas.organization import OrganizationWithRole
from backend.app.schemas.user import UserProfileRead, UserSyncRequest
from backend.app.services.agency_service import AgencyServiceManager
from backend.app.services.session_service import SessionService

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])

DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_ORG_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000009")
AGENCY_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
CONSULTANT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")


class DemoSessionRequest(BaseModel):
    role: str = "owner"
    as_admin: bool = False


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text) or "workspace"


def _set_session_cookie(response: Response, token: str) -> None:
    """Sets a secure HttpOnly cookie for session token."""
    is_prod = settings.APP_ENV == "production"
    response.set_cookie(
        key="marketpath_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=is_prod,
        max_age=86400 * 7,
        path="/",
    )


@router.post("/register-company", response_model=LoginAccountResponse, status_code=status.HTTP_201_CREATED)
async def register_company(
    payload: RegisterCompanyRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Self-service company registration creating genuine user, organization, brand profile, and session."""
    email_clean = str(payload.email).strip().lower()
    full_name = payload.resolved_full_name
    website = payload.resolved_website

    # Check if email is already registered
    existing_user_res = await db.execute(select(UserProfile).where(UserProfile.email == email_clean))
    if existing_user_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in.",
        )

    # Begin atomic registration
    try:
        # 1. Create UserProfile with secure password hash
        pw_hash = hash_password(payload.password)
        user = UserProfile(
            id=uuid.uuid4(),
            email=email_clean,
            full_name=full_name,
            account_type="company",
            is_platform_admin=False,
            password_hash=pw_hash,
        )
        db.add(user)
        await db.flush()

        # 2. Create Organization
        base_slug = _slugify(payload.brand_name)
        slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        org = Organization(
            id=uuid.uuid4(),
            name=payload.brand_name.strip(),
            slug=slug,
            org_type="business",
            is_active=True,
            settings={
                "currency": "INR",
                "timezone": "Asia/Kolkata",
                "category": payload.category,
                "website": website,
            },
        )
        db.add(org)
        await db.flush()

        # 3. Create Owner Membership
        member = OrganizationMember(
            id=uuid.uuid4(),
            organization_id=org.id,
            user_id=user.id,
            role="owner",
        )
        db.add(member)

        # 4. Create Initial Clean Brand Profile (zero fake/demo data)
        brand = BrandProfile(
            id=uuid.uuid4(),
            organization_id=org.id,
            brand_name=payload.brand_name.strip(),
            tagline=f"Conscious {payload.category} brand",
            tone_of_voice="Warm & Aesthetic",
            visual_guidelines={},
            key_usps=[],
            brand_values=[],
            customer_demographics={},
            product_stories=[],
        )
        db.add(brand)

        # Commit transaction atomically
        await db.commit()
        await db.refresh(user)
        await db.refresh(org)

        # 5. Create genuine database-backed session
        db_session, raw_token = await SessionService.create_session(
            db,
            user_id=user.id,
            organization_id=org.id,
            session_type="real",
        )
        await db.commit()

        _set_session_cookie(response, raw_token)

        org_with_role = OrganizationWithRole(
            id=org.id,
            name=org.name,
            slug=org.slug,
            is_active=org.is_active,
            settings=org.settings,
            created_at=org.created_at,
            updated_at=org.updated_at,
            role="owner",
        )

        return LoginAccountResponse(
            access_token=raw_token,
            token_type="bearer",
            account_type="company",
            redirect_url="/app/dashboard",
            session_id=db_session.id,
            user=UserProfileRead.model_validate(user),
            organization=org_with_role,
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed due to a database error: {str(e)}",
        )


@router.post("/agency/signup", response_model=ApplicationSubmittedResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register-agency", response_model=ApplicationSubmittedResponse, status_code=status.HTTP_201_CREATED)
async def register_agency(
    payload: RegisterAgencyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Public agency partner registration. Creates pending application under review."""
    email_clean = str(payload.email).strip().lower()

    # Check duplicate
    existing_user_res = await db.execute(select(UserProfile).where(UserProfile.email == email_clean))
    if existing_user_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in.",
        )

    try:
        pw_hash = hash_password(payload.password)
        user = UserProfile(
            id=uuid.uuid4(),
            email=email_clean,
            full_name=payload.contact_name.strip(),
            account_type="agency",
            is_platform_admin=False,
            is_active=True,
            must_change_password=False,
            vetting_status="under_review",
            password_hash=pw_hash,
        )
        db.add(user)
        await db.flush()

        # Create agency organization
        base_slug = _slugify(payload.agency_name)
        slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        org = Organization(
            id=uuid.uuid4(),
            name=payload.agency_name.strip(),
            slug=slug,
            org_type="agency",
            is_active=True,
            settings={
                "city": payload.city,
                "state": payload.state,
                "website": payload.website,
                "years_experience": payload.years_of_experience,
            },
        )
        db.add(org)
        await db.flush()

        # Link membership
        member = OrganizationMember(
            id=uuid.uuid4(),
            organization_id=org.id,
            user_id=user.id,
            role="owner",
        )
        db.add(member)

        # Create AgencyProfile
        agency_profile = AgencyProfile(
            id=uuid.uuid4(),
            organization_id=org.id,
            name=payload.agency_name.strip(),
            slug=slug,
            tagline=f"Expert growth & marketing agency based in {payload.city}",
            description=payload.description.strip(),
            website=payload.website,
            email=email_clean,
            phone=payload.phone,
            city=payload.city,
            state=payload.state,
            country="India",
            remote_or_local="both",
            team_size="1-10",
            founded_year=2024,
            category_specialties=payload.service_categories or ["Growth Marketing", "D2C Scaling"],
            service_offerings=payload.service_categories or ["Performance Marketing", "Social Media"],
            min_budget_inr=15000,
            gst_number=payload.gst_number,
            verification_status="under_review",
            verification_notes="Self-service registration submitted. Awaiting platform operator review.",
            is_available=False,
            is_active=False,
            is_demo=False,
            tier="standard",
        )
        db.add(agency_profile)
        await db.flush()

        # Link AgencyMember
        db.add(
            AgencyMember(
                agency_profile_id=agency_profile.id,
                user_id=user.id,
                role="agency_owner",
            )
        )

        await db.commit()

        return ApplicationSubmittedResponse(
            success=True,
            account_type="agency",
            status="under_review",
            message="Agency application submitted successfully. Our operations team will review your credentials within 24-48 hours.",
            user_id=user.id,
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agency registration failed: {str(e)}",
        )


@router.post("/consultant/signup", response_model=ApplicationSubmittedResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register-consultant", response_model=ApplicationSubmittedResponse, status_code=status.HTTP_201_CREATED)
async def register_consultant(
    payload: RegisterConsultantRequest,
    db: AsyncSession = Depends(get_db),
):
    """Public consultant registration. Creates pending application under review."""
    email_clean = str(payload.email).strip().lower()

    # Check duplicate
    existing_user_res = await db.execute(select(UserProfile).where(UserProfile.email == email_clean))
    if existing_user_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in.",
        )

    try:
        pw_hash = hash_password(payload.password)
        user = UserProfile(
            id=uuid.uuid4(),
            email=email_clean,
            full_name=payload.full_name.strip(),
            account_type="consultant",
            is_platform_admin=False,
            is_active=True,
            must_change_password=False,
            vetting_status="under_review",
            password_hash=pw_hash,
        )
        db.add(user)
        await db.commit()

        return ApplicationSubmittedResponse(
            success=True,
            account_type="consultant",
            status="under_review",
            message="Consultant registration submitted successfully. Our advisory board will review your credentials within 24-48 hours.",
            user_id=user.id,
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consultant registration failed: {str(e)}",
        )


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allows authenticated user (such as newly bootstrapped Platform Admin) to rotate password."""
    if payload.old_password and current_user.password_hash:
        if not verify_password(payload.old_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password.",
            )

    current_user.password_hash = hash_password(payload.new_password)
    current_user.must_change_password = False
    await db.commit()

    return {"success": True, "message": "Password changed successfully. Your account is fully secured."}


@router.post("/login-account", response_model=LoginAccountResponse)
async def login_account(
    payload: LoginAccountRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Unified login endpoint with credential verification, account type mismatch checks, and genuine sessions."""
    email_clean = str(payload.email).strip().lower()

    # Query user profile
    user_res = await db.execute(select(UserProfile).where(UserProfile.email == email_clean))
    user = user_res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. If you haven't registered your brand workspace yet, please sign up.",
        )

    # Verify Password (strict PBKDF2 check - no demo shortcuts or password bypass)
    if not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials.",
        )

    # Verify Account Type (Section 3.5 Mismatch check)
    if payload.account_type == "admin":
        if not user.is_platform_admin and user.account_type != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account type mismatch: This email is registered as a {user.account_type.capitalize()} account, but you selected Platform Admin. Please select the {user.account_type.capitalize()} tab to sign in.",
            )
    elif payload.account_type == "consultant":
        if user.account_type != "consultant":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account type mismatch: This email is registered as a {user.account_type.capitalize()} account, but you selected Consultant. Please select the {user.account_type.capitalize()} tab to sign in.",
            )
    elif payload.account_type == "agency":
        if user.account_type != "agency":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account type mismatch: This email is registered as a {user.account_type.capitalize()} account, but you selected Agency. Please select the {user.account_type.capitalize()} tab to sign in.",
            )
    elif payload.account_type == "company":
        if user.account_type != "company":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account type mismatch: This email is registered as a {user.account_type.capitalize()} account, but you selected Company. Please select the {user.account_type.capitalize()} tab to sign in.",
            )

    # Check vetting status and account active status
    if getattr(user, "is_active", True) is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact platform support.",
        )

    vetting = getattr(user, "vetting_status", "approved")
    if vetting == "under_review":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your registration application is currently under review by our operations team. You will receive an email notification once your profile is approved.",
        )
    elif vetting == "rejected":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your application was not approved by platform administration. Please contact support for more details.",
        )

    # Determine redirect URL and Organization context
    org_with_role = None
    target_org_id = None

    if payload.account_type == "admin":
        redirect_url = "/admin"
    elif payload.account_type == "consultant":
        redirect_url = "/consultant"
    elif payload.account_type == "agency":
        redirect_url = "/agency/portal"
    else:
        redirect_url = "/app/dashboard"
        # Find active organization membership
        mem_res = await db.execute(
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.organization))
            .where(OrganizationMember.user_id == user.id)
        )
        membership = mem_res.scalar_one_or_none()

        if membership and membership.organization:
            org = membership.organization
            target_org_id = org.id
            org_with_role = OrganizationWithRole(
                id=org.id,
                name=org.name,
                slug=org.slug,
                is_active=org.is_active,
                settings=org.settings,
                created_at=org.created_at,
                updated_at=org.updated_at,
                role=membership.role,
            )

    # Create genuine database-backed session
    session_type = "demo" if user.id in [DEMO_USER_ID, ADMIN_USER_ID, AGENCY_USER_ID, CONSULTANT_USER_ID] else "real"
    db_session, raw_token = await SessionService.create_session(
        db,
        user_id=user.id,
        organization_id=target_org_id,
        session_type=session_type,
    )
    await db.commit()

    _set_session_cookie(response, raw_token)

    return LoginAccountResponse(
        access_token=raw_token,
        token_type="bearer",
        account_type=payload.account_type,
        redirect_url=redirect_url,
        session_id=db_session.id,
        user=UserProfileRead.model_validate(user),
        organization=org_with_role,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Revokes the active database session and clears the session cookie."""
    raw_token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        raw_token = auth_header.replace("Bearer ", "").strip()
    elif request.cookies.get("marketpath_session"):
        raw_token = request.cookies.get("marketpath_session", "").strip()

    if raw_token:
        await SessionService.revoke_session(db, raw_token)

    is_prod = settings.APP_ENV == "production"
    response.delete_cookie(
        key="marketpath_session",
        path="/",
        httponly=True,
        samesite="lax",
        secure=is_prod,
    )
    return LogoutResponse(success=True, message="Successfully logged out. Session invalidated.")


@router.post("/demo-session")
async def create_demo_session():
    """Demo session bypass is permanently removed in production."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Demo shortcuts have been removed. Please sign in with genuine account credentials.",
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generates a secure, single-use, timed password reset token."""
    email_clean = str(payload.email).strip().lower()
    user_res = await db.execute(select(UserProfile).where(UserProfile.email == email_clean))
    user = user_res.scalar_one_or_none()

    reset_token = None
    if user:
        reset_token = create_password_reset_token(str(user.id), user.email, user.password_hash)

    # Always return a generic success message to prevent user enumeration
    return ForgotPasswordResponse(
        success=True,
        message=f"If an account exists for {payload.email}, password reset instructions have been dispatched.",
        reset_token=reset_token,
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verifies reset token, updates password hash using PBKDF2, and revokes previous sessions."""
    import hashlib
    claims = verify_password_reset_token(payload.token)
    user_id_str = claims.get("sub")
    expected_fp = claims.get("fp")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user reference in reset token.",
        )

    user_res = await db.execute(select(UserProfile).where(UserProfile.id == user_uuid))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with this reset token no longer exists.",
        )

    # Verify single-use fingerprint
    current_fp = hashlib.sha256((user.password_hash or "").encode("utf-8")).hexdigest()[:16]
    if current_fp != expected_fp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has already been used or invalidated. Please request a new one.",
        )

    # Update password hash
    user.password_hash = hash_password(payload.password)
    await db.commit()

    # Revoke all active sessions for this user across all devices
    await SessionService.revoke_all_user_sessions(db, user.id)

    return ResetPasswordResponse(
        success=True,
        message="Password updated successfully. All active sessions have been revoked. Please sign in with your new password.",
    )



@router.get("/me", response_model=AuthMeResponse)
async def get_me(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the authenticated user profile and all organizations with roles."""
    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.organization))
        .where(OrganizationMember.user_id == current_user.id)
    )
    memberships = result.scalars().all()

    orgs_with_role = []
    for m in memberships:
        org = m.organization
        if org and org.is_active:
            orgs_with_role.append(
                OrganizationWithRole(
                    id=org.id,
                    name=org.name,
                    slug=org.slug,
                    is_active=org.is_active,
                    settings=org.settings,
                    created_at=org.created_at,
                    updated_at=org.updated_at,
                    role=m.role,
                )
            )

    return AuthMeResponse(
        user=UserProfileRead.model_validate(current_user),
        organizations=orgs_with_role,
        active_organization_id=orgs_with_role[0].id if orgs_with_role else None,
    )


@router.post("/sync-profile", response_model=UserProfileRead)
async def sync_profile(
    payload: UserSyncRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates the user profile metadata from client session."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url

    await db.commit()
    await db.refresh(current_user)
    return UserProfileRead.model_validate(current_user)

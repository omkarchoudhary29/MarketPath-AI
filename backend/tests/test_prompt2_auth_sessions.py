import pytest
from httpx import AsyncClient
from sqlalchemy import select
from backend.app.models.user import UserProfile
from backend.app.models.session import UserSession
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.brand import BrandProfile
from backend.app.core.security import verify_password


@pytest.mark.asyncio
async def test_company_registration_success(client: AsyncClient, db_session):
    """Verifies that real company registration creates user, org, membership, brand, and session."""
    payload = {
        "brand_name": "Sanskriti Living",
        "category": "Home & Living / Decor",
        "founder_name": "Rohit Verma",
        "email": "rohit.verma@sanskritiliving.in",
        "password": "SecurePassword123!",
        "website_url": "https://sanskritiliving.in",
    }

    res = await client.post("/api/v1/auth/register-company", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "rohit.verma@sanskritiliving.in"
    assert data["user"]["full_name"] == "Rohit Verma"
    assert data["user"]["account_type"] == "company"
    assert data["user"]["is_platform_admin"] is False
    assert data["organization"]["name"] == "Sanskriti Living"
    assert data["organization"]["role"] == "owner"
    assert data["redirect_url"] == "/app/dashboard"
    assert "session_id" in data

    # Verify session cookie was set
    assert "marketpath_session" in res.cookies

    # Verify database state
    user_stmt = select(UserProfile).where(UserProfile.email == "rohit.verma@sanskritiliving.in")
    result = await db_session.execute(user_stmt)
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.password_hash is not None
    assert verify_password("SecurePassword123!", db_user.password_hash) is True
    assert db_user.account_type == "company"

    # Verify organization and membership
    org_stmt = select(Organization).where(Organization.name == "Sanskriti Living")
    org_result = await db_session.execute(org_stmt)
    db_org = org_result.scalar_one_or_none()
    assert db_org is not None

    mem_stmt = select(OrganizationMember).where(
        OrganizationMember.user_id == db_user.id,
        OrganizationMember.organization_id == db_org.id,
    )
    mem_result = await db_session.execute(mem_stmt)
    db_mem = mem_result.scalar_one_or_none()
    assert db_mem is not None
    assert db_mem.role == "owner"

    # Verify brand profile
    brand_stmt = select(BrandProfile).where(BrandProfile.organization_id == db_org.id)
    brand_result = await db_session.execute(brand_stmt)
    db_brand = brand_result.scalar_one_or_none()
    assert db_brand is not None
    assert db_brand.brand_name == "Sanskriti Living"

    # Verify active session
    sess_stmt = select(UserSession).where(UserSession.user_id == db_user.id)
    sess_result = await db_session.execute(sess_stmt)
    db_sess = sess_result.scalar_one_or_none()
    assert db_sess is not None
    assert db_sess.is_active is True


@pytest.mark.asyncio
async def test_company_registration_duplicate_email(client: AsyncClient):
    """Verifies that attempting duplicate registration returns 409 Conflict."""
    payload = {
        "brand_name": "Sanskriti Living",
        "category": "Home & Living / Decor",
        "founder_name": "Rohit Verma",
        "email": "duplicate@sanskritiliving.in",
        "password": "SecurePassword123!",
    }

    res1 = await client.post("/api/v1/auth/register-company", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/auth/register-company", json=payload)
    assert res2.status_code == 409
    msg = res2.json().get("detail") or res2.json().get("error", {}).get("message", "")
    assert "already exists" in msg.lower() or "already registered" in msg.lower()


@pytest.mark.asyncio
async def test_login_password_verification(client: AsyncClient):
    """Verifies that login enforces password verification using PBKDF2 hashing."""
    reg_payload = {
        "brand_name": "Pure Ayurveda",
        "category": "Clean Skincare & Beauty",
        "founder_name": "Devi Sharma",
        "email": "devi@pureayurveda.in",
        "password": "CorrectSecret456!",
    }
    reg_res = await client.post("/api/v1/auth/register-company", json=reg_payload)
    assert reg_res.status_code == 201

    # Login with wrong password
    bad_login = await client.post(
        "/api/v1/auth/login-account",
        json={
            "email": "devi@pureayurveda.in",
            "password": "WrongPassword!",
            "account_type": "company",
        },
    )
    assert bad_login.status_code == 401
    err_msg = bad_login.json().get("detail") or bad_login.json().get("error", {}).get("message", "")
    assert "invalid email or password" in err_msg.lower()

    # Login with correct password
    good_login = await client.post(
        "/api/v1/auth/login-account",
        json={
            "email": "devi@pureayurveda.in",
            "password": "CorrectSecret456!",
            "account_type": "company",
        },
    )
    assert good_login.status_code == 200
    assert "access_token" in good_login.json()
    assert good_login.json()["redirect_url"] == "/app/dashboard"


@pytest.mark.asyncio
async def test_account_type_mismatch_prevention(client: AsyncClient):
    """Verifies that users cannot log in under an account type they do not possess."""
    reg_payload = {
        "brand_name": "Kashmir Crafts",
        "category": "Indian Regional Heritage Crafts",
        "founder_name": "Zainab Shah",
        "email": "zainab@kashmircrafts.in",
        "password": "SecureCrafts123!",
    }
    reg_res = await client.post("/api/v1/auth/register-company", json=reg_payload)
    assert reg_res.status_code == 201

    # Try logging in as admin
    admin_mismatch = await client.post(
        "/api/v1/auth/login-account",
        json={
            "email": "zainab@kashmircrafts.in",
            "password": "SecureCrafts123!",
            "account_type": "admin",
        },
    )
    assert admin_mismatch.status_code == 403
    err_msg1 = admin_mismatch.json().get("detail") or admin_mismatch.json().get("error", {}).get("message", "")
    assert "cannot log in as 'admin'" in err_msg1.lower() or "mismatch" in err_msg1.lower()

    # Try logging in as agency
    agency_mismatch = await client.post(
        "/api/v1/auth/login-account",
        json={
            "email": "zainab@kashmircrafts.in",
            "password": "SecureCrafts123!",
            "account_type": "agency",
        },
    )
    assert agency_mismatch.status_code == 403
    err_msg2 = agency_mismatch.json().get("detail") or agency_mismatch.json().get("error", {}).get("message", "")
    assert "cannot log in as 'agency'" in err_msg2.lower() or "mismatch" in err_msg2.lower()

    # Try logging in as consultant
    consultant_mismatch = await client.post(
        "/api/v1/auth/login-account",
        json={
            "email": "zainab@kashmircrafts.in",
            "password": "SecureCrafts123!",
            "account_type": "consultant",
        },
    )
    assert consultant_mismatch.status_code == 403
    err_msg3 = consultant_mismatch.json().get("detail") or consultant_mismatch.json().get("error", {}).get("message", "")
    assert "cannot log in as 'consultant'" in err_msg3.lower() or "mismatch" in err_msg3.lower()


@pytest.mark.asyncio
async def test_all_account_types_login(client: AsyncClient, db_session):
    """Verifies login for all four account types with correct redirect routing."""
    import uuid
    from backend.app.core.security import hash_password

    pw_hash = hash_password("marketpath123")

    # Seed isolated test accounts for all four types
    c_user = UserProfile(
        id=uuid.uuid4(),
        email="test.company@platform.in",
        full_name="Company Owner",
        account_type="company",
        is_platform_admin=False,
        password_hash=pw_hash,
    )
    c_org = Organization(
        id=uuid.uuid4(),
        name="Test Brand Co",
        slug="test-brand-co",
        org_type="business",
        is_active=True,
        settings={"currency": "INR", "category": "Home"},
    )
    c_mem = OrganizationMember(
        id=uuid.uuid4(),
        organization_id=c_org.id,
        user_id=c_user.id,
        role="owner",
    )
    a_user = UserProfile(
        id=uuid.uuid4(),
        email="test.agency@growth.in",
        full_name="Agency Partner",
        account_type="agency",
        is_platform_admin=False,
        password_hash=pw_hash,
    )
    cons_user = UserProfile(
        id=uuid.uuid4(),
        email="test.consultant@advisory.in",
        full_name="Lead Consultant",
        account_type="consultant",
        is_platform_admin=False,
        password_hash=pw_hash,
    )
    adm_user = UserProfile(
        id=uuid.uuid4(),
        email="test.admin@marketpath.ai",
        full_name="Platform Operator",
        account_type="admin",
        is_platform_admin=True,
        password_hash=pw_hash,
    )
    db_session.add_all([c_user, c_org, c_mem, a_user, cons_user, adm_user])
    await db_session.commit()

    # 1. Company
    res_company = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "test.company@platform.in", "password": "marketpath123", "account_type": "company"},
    )
    assert res_company.status_code == 200
    assert res_company.json()["redirect_url"] == "/app/dashboard"
    assert res_company.json()["user"]["account_type"] == "company"

    # 2. Agency
    res_agency = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "test.agency@growth.in", "password": "marketpath123", "account_type": "agency"},
    )
    assert res_agency.status_code == 200
    assert res_agency.json()["redirect_url"] == "/agency/portal"
    assert res_agency.json()["user"]["account_type"] == "agency"

    # 3. Consultant
    res_consultant = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "test.consultant@advisory.in", "password": "marketpath123", "account_type": "consultant"},
    )
    assert res_consultant.status_code == 200
    assert res_consultant.json()["redirect_url"] == "/consultant"
    assert res_consultant.json()["user"]["account_type"] == "consultant"

    # 4. Admin
    res_admin = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "test.admin@marketpath.ai", "password": "marketpath123", "account_type": "admin"},
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["redirect_url"] == "/admin"
    assert res_admin.json()["user"]["is_platform_admin"] is True


@pytest.mark.asyncio
async def test_logout_revokes_database_session(client: AsyncClient, db_session):
    """Verifies that logout invalidates the database session and rejects subsequent authenticated calls."""
    import uuid
    from backend.app.core.security import hash_password

    # Seed test user
    test_user = UserProfile(
        id=uuid.uuid4(),
        email="logout.test@brand.in",
        full_name="Logout Test User",
        account_type="company",
        is_platform_admin=False,
        password_hash=hash_password("marketpath123"),
    )
    db_session.add(test_user)
    await db_session.commit()

    login_res = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "logout.test@brand.in", "password": "marketpath123", "account_type": "company"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    user_id = login_res.json()["user"]["id"]

    # Verify authenticated access works
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200

    # Logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Subsequent access with the same token must now be rejected
    subsequent_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert subsequent_res.status_code == 401


@pytest.mark.asyncio
async def test_new_company_workspace_isolation(client: AsyncClient):
    """Verifies that newly registered companies have an isolated workspace with 0 products and 0 orders."""
    reg_payload = {
        "brand_name": "Organic Vedic",
        "category": "Organic Food & Gourmet Staples",
        "founder_name": "Karan Malhotra",
        "email": "karan@organicvedic.in",
        "password": "VedicPassword789!",
    }
    reg_res = await client.post("/api/v1/auth/register-company", json=reg_payload)
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    org_id = reg_res.json()["organization"]["id"]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-Id": org_id,
    }

    # Products should be empty
    prod_res = await client.get("/api/v1/products", headers=headers)
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    if isinstance(prod_data, dict) and "items" in prod_data:
        assert len(prod_data["items"]) == 0
    elif isinstance(prod_data, list):
        assert len(prod_data) == 0

    # Orders should be empty
    orders_res = await client.get("/api/v1/orders", headers=headers)
    assert orders_res.status_code == 200
    orders_data = orders_res.json()
    if isinstance(orders_data, dict) and "items" in orders_data:
        assert len(orders_data["items"]) == 0
    elif isinstance(orders_data, list):
        assert len(orders_data) == 0


@pytest.mark.asyncio
async def test_demo_session_endpoint_disabled(client: AsyncClient):
    """Verifies that the demo-session shortcut endpoint is disabled with 403 Forbidden."""
    res = await client.post("/api/v1/auth/demo-session", json={})
    assert res.status_code == 403
    assert "demo shortcuts have been removed" in res.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_unknown_email_rejected_without_demo_fallback(client: AsyncClient):
    """Verifies that an unknown email is rejected with 401 and not silently converted to a demo user."""
    res = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "nonexistent.user.random999@unknownbrand.xyz", "password": "randompassword123", "account_type": "company"},
    )
    assert res.status_code == 401
    msg = res.json().get("detail", "")
    assert "invalid email or password" in msg.lower()


@pytest.mark.asyncio
async def test_forgot_password_and_reset_flow(client: AsyncClient):
    """Verifies end-to-end password reset: forgot-password -> token -> reset-password -> login."""
    # 1. Register a test company
    reg_payload = {
        "brand_name": "Kashi Organics",
        "category": "Organic Food & Gourmet Staples",
        "founder_name": "Devendra Nath",
        "email": "devendra@kashiorganics.in",
        "password": "OriginalPassword123!",
    }
    reg_res = await client.post("/api/v1/auth/register-company", json=reg_payload)
    assert reg_res.status_code == 201

    # 2. Request forgot-password token
    forgot_res = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "devendra@kashiorganics.in"},
    )
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json().get("reset_token")
    assert reset_token is not None

    # 3. Reset password using token
    reset_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "password": "NewSecurePassword456!"},
    )
    assert reset_res.status_code == 200
    assert reset_res.json()["success"] is True

    # 4. Old password must now fail
    old_login = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "devendra@kashiorganics.in", "password": "OriginalPassword123!", "account_type": "company"},
    )
    assert old_login.status_code == 401

    # 5. New password must succeed
    new_login = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "devendra@kashiorganics.in", "password": "NewSecurePassword456!", "account_type": "company"},
    )
    assert new_login.status_code == 200
    assert new_login.json()["user"]["email"] == "devendra@kashiorganics.in"

    # 6. Reusing the same reset token must fail (single-use enforcement)
    reused_reset = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "password": "AnotherPassword789!"},
    )
    assert reused_reset.status_code == 400
    assert "already been used" in reused_reset.json().get("detail", "").lower()


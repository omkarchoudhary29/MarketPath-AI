import json
import os
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from backend.app.core.security import hash_password, hash_session_token
from backend.app.models.user import UserProfile
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.session import UserSession
from backend.app.models.chat import AIConversation, AIChatMessage
from backend.app.models.catalogue import Product


@pytest.mark.asyncio
async def test_two_independent_companies_isolation_and_ai_memory(client: AsyncClient, db_session):
    """Verifies that Account A and Account B have strictly isolated data, products, and persistent AI conversations."""
    # 1. Register Account A
    payload_a = {
        "brand_name": "Kavya Naturals",
        "category": "Beauty & Personal Care",
        "founder_name": "Kavya Patel",
        "email": "kavya@kavyanaturals.in",
        "password": "StrongPasswordA1!",
        "website_url": "https://kavyanaturals.in",
    }
    res_a = await client.post("/api/v1/auth/register-company", json=payload_a)
    assert res_a.status_code == 201
    data_a = res_a.json()
    token_a = data_a["access_token"]
    user_id_a = data_a["user"]["id"]
    org_id_a = data_a["organization"]["id"]

    # 2. Register Account B
    payload_b = {
        "brand_name": "Tarun Craftwares",
        "category": "Home & Decor",
        "founder_name": "Tarun Mehta",
        "email": "tarun@taruncraftwares.in",
        "password": "StrongPasswordB1!",
        "website_url": "https://taruncraftwares.in",
    }
    res_b = await client.post("/api/v1/auth/register-company", json=payload_b)
    assert res_b.status_code == 201
    data_b = res_b.json()
    token_b = data_b["access_token"]
    user_id_b = data_b["user"]["id"]
    org_id_b = data_b["organization"]["id"]

    # Verify completely distinct User and Organization IDs
    assert user_id_a != user_id_b
    assert org_id_a != org_id_b

    # 3. Create a product in Account A's catalogue
    prod_payload_a = {
        "sku": "KVY-OIL-001",
        "title": "Kavya Kumkumadi Face Oil",
        "category": "Beauty & Personal Care",
        "status": "active",
        "base_price": 1299.0,
        "cost_price": 450.0,
    }
    prod_res_a = await client.post(
        "/api/v1/products",
        json=prod_payload_a,
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-Id": org_id_a},
    )
    assert prod_res_a.status_code == 201

    # Verify Account B cannot see Account A's product
    list_res_b = await client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-Id": org_id_b},
    )
    assert list_res_b.status_code == 200
    assert len(list_res_b.json()["items"]) == 0

    # 4. Verify Persistent AI Assistant Memory and Isolation
    # Account A sends an operational inquiry
    chat_payload_a = {
        "message": "How does inventory sync work across channels?",
        "current_page": "/app/products",
        "history": [],
    }
    chat_res_a = await client.post(
        "/api/v1/support/chat",
        json=chat_payload_a,
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-Id": org_id_a},
    )
    assert chat_res_a.status_code == 200
    assert "inventory" in chat_res_a.json()["answer"].lower()

    # Account B queries chat history -> MUST be empty (zero leakage from Account A)
    hist_res_b = await client.get(
        "/api/v1/support/chat/history",
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-Id": org_id_b},
    )
    assert hist_res_b.status_code == 200
    assert len(hist_res_b.json()["messages"]) == 0

    # Account A queries chat history -> MUST contain Account A's query and bot response
    hist_res_a = await client.get(
        "/api/v1/support/chat/history",
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-Id": org_id_a},
    )
    assert hist_res_a.status_code == 200
    msgs_a = hist_res_a.json()["messages"]
    assert len(msgs_a) == 2
    assert msgs_a[0]["sender"] == "user"
    assert "inventory" in msgs_a[0]["text"]
    assert msgs_a[1]["sender"] == "bot"

    # 5. Verify Sensitive Credential Redaction in AI Memory
    chat_cred_payload = {
        "message": "My database password is password=SuperSecretPassword123! and token is Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "current_page": "/app/dashboard",
        "history": [],
    }
    await client.post(
        "/api/v1/support/chat",
        json=chat_cred_payload,
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-Id": org_id_a},
    )

    # Inspect database records directly
    db_msgs = (await db_session.execute(
        select(AIChatMessage).order_by(AIChatMessage.created_at.desc())
    )).scalars().all()
    recent_user_msg = next(m for m in db_msgs if m.sender == "user")
    assert "SuperSecretPassword123!" not in recent_user_msg.message_text
    assert "[REDACTED_CREDENTIAL]" in recent_user_msg.message_text

    # 6. Logout Account A and Log Back In -> Verify Persistent Restoration
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert logout_res.status_code == 200

    # Log back in as Account A
    login_res_a = await client.post(
        "/api/v1/auth/login-account",
        json={
            "email": "kavya@kavyanaturals.in",
            "password": "StrongPasswordA1!",
            "account_type": "company",
        },
    )
    assert login_res_a.status_code == 200
    new_token_a = login_res_a.json()["access_token"]

    # Verify Account A's catalogue product is still present
    relogin_products = await client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {new_token_a}", "X-Organization-Id": org_id_a},
    )
    assert relogin_products.status_code == 200
    assert len(relogin_products.json()["items"]) == 1
    assert relogin_products.json()["items"][0]["sku"] == "KVY-OIL-001"

    # Verify Account A's AI conversation history is restored from database
    relogin_chat = await client.get(
        "/api/v1/support/chat/history",
        headers={"Authorization": f"Bearer {new_token_a}", "X-Organization-Id": org_id_a},
    )
    assert relogin_chat.status_code == 200
    assert len(relogin_chat.json()["messages"]) >= 2


@pytest.mark.asyncio
async def test_genuine_session_lifecycle(client: AsyncClient, db_session):
    """Verifies session creation, refresh persistence, logout revocation, expired session, and invalid token rejection."""
    # Register user
    reg_payload = {
        "brand_name": "Devi Organics",
        "category": "Food & Beverage",
        "founder_name": "Devi Prasad",
        "email": "devi.prasad@deviorganics.in",
        "password": "DeviPassword123!",
    }
    reg_res = await client.post("/api/v1/auth/register-company", json=reg_payload)
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    user_id = uuid.UUID(reg_res.json()["user"]["id"])

    # 1. Session creation verified in database
    token_hash = hash_session_token(token)
    session_stmt = select(UserSession).where(UserSession.token_hash == token_hash)
    db_session_obj = (await db_session.execute(session_stmt)).scalar_one_or_none()
    assert db_session_obj is not None
    assert db_session_obj.user_id == user_id
    assert db_session_obj.is_active is True

    # 2. Browser refresh persistence via /me endpoint
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == "devi.prasad@deviorganics.in"

    # 3. Invalid token rejection
    bad_res = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer completely_invalid_token_12345"})
    assert bad_res.status_code == 401

    # 4. Expired session rejection
    # Manually expire session
    db_session_obj.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.commit()

    expired_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert expired_res.status_code == 401
    assert "expired" in expired_res.json()["detail"].lower()

    # 5. Logout revocation
    # Issue a fresh valid login
    login_res = await client.post(
        "/api/v1/auth/login-account",
        json={
            "email": "devi.prasad@deviorganics.in",
            "password": "DeviPassword123!",
            "account_type": "company",
        },
    )
    assert login_res.status_code == 200
    fresh_token = login_res.json()["access_token"]

    # Verify active
    check_active = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fresh_token}"})
    assert check_active.status_code == 200

    # Logout
    logout_res = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {fresh_token}"})
    assert logout_res.status_code == 200

    # Verify revoked
    revoked_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fresh_token}"})
    assert revoked_res.status_code == 401


@pytest.mark.asyncio
async def test_provisioned_roles_permissions_with_vault(client: AsyncClient, db_session):
    """Verifies Agency, Consultant, and Admin role permissions using provisioned accounts with vault credentials."""
    vault_path = "test_credentials_vault.json"
    if os.path.exists(vault_path):
        with open(vault_path, "r") as f:
            vault = json.load(f)
    else:
        vault = {
            "agency@marketpath.ai": "TestPass#Agency2026",
            "consultant@marketpath.ai": "TestPass#Consultant2026",
            "operator@marketpath.ai": "TestPass#Admin2026",
        }

    # Seed provisioned users into test in-memory database with hashes matching vault
    agency_pwd = vault["agency@marketpath.ai"]
    consultant_pwd = vault["consultant@marketpath.ai"]
    operator_pwd = vault["operator@marketpath.ai"]

    agency_user = UserProfile(
        id=uuid.uuid4(),
        email="agency@marketpath.ai",
        full_name="Agency Growth Partner",
        account_type="agency",
        is_platform_admin=False,
        password_hash=hash_password(agency_pwd),
    )
    consultant_user = UserProfile(
        id=uuid.uuid4(),
        email="consultant@marketpath.ai",
        full_name="Senior D2C Consultant",
        account_type="consultant",
        is_platform_admin=False,
        password_hash=hash_password(consultant_pwd),
    )
    admin_user = UserProfile(
        id=uuid.uuid4(),
        email="operator@marketpath.ai",
        full_name="Platform Operator",
        account_type="admin",
        is_platform_admin=True,
        password_hash=hash_password(operator_pwd),
    )
    db_session.add_all([agency_user, consultant_user, admin_user])
    await db_session.commit()

    # 1. Agency Login & Verification
    agency_login = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "agency@marketpath.ai", "password": agency_pwd, "account_type": "agency"},
    )
    assert agency_login.status_code == 200
    agency_data = agency_login.json()
    assert agency_data["user"]["account_type"] == "agency"
    assert agency_data["redirect_url"] == "/agency/portal"
    agency_token = agency_data["access_token"]

    # Agency cannot access Admin endpoints
    admin_attempt = await client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {agency_token}"},
    )
    assert admin_attempt.status_code == 403

    # 2. Consultant Login & Verification
    consultant_login = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "consultant@marketpath.ai", "password": consultant_pwd, "account_type": "consultant"},
    )
    assert consultant_login.status_code == 200
    consultant_data = consultant_login.json()
    assert consultant_data["user"]["account_type"] == "consultant"
    assert consultant_data["redirect_url"] == "/consultant"
    consultant_token = consultant_data["access_token"]

    # Consultant cannot access Admin endpoints
    admin_attempt_consultant = await client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {consultant_token}"},
    )
    assert admin_attempt_consultant.status_code == 403

    # 3. Platform Admin Login & Verification
    admin_login = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "operator@marketpath.ai", "password": operator_pwd, "account_type": "admin"},
    )
    assert admin_login.status_code == 200
    admin_data = admin_login.json()
    assert admin_data["user"]["account_type"] == "admin"
    assert admin_data["user"]["is_platform_admin"] is True
    assert admin_data["redirect_url"] == "/admin"
    admin_token = admin_data["access_token"]

    # Admin CAN access Admin telemetry
    admin_access = await client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_access.status_code == 200
    assert "total_users" in admin_access.json()


@pytest.mark.asyncio
async def test_demo_functionality_strictly_disabled(client: AsyncClient):
    """Verifies that demo endpoints and bypasses are completely disabled."""
    # 1. /demo-session endpoint disabled
    demo_res = await client.post("/api/v1/auth/demo-session", json={"role": "company"})
    assert demo_res.status_code == 403
    assert "removed" in demo_res.json()["detail"].lower()

    # 2. Unregistered user login rejected with 401 (no fallback)
    bad_login = await client.post(
        "/api/v1/auth/login-account",
        json={"email": "nonexistent@user.com", "password": "anypassword", "account_type": "company"},
    )
    assert bad_login.status_code == 401
    assert "invalid" in bad_login.json()["detail"].lower()

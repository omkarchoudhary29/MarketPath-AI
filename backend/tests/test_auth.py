import uuid
import pytest
from httpx import AsyncClient
from backend.app.core.security import encrypt_token, decrypt_token


@pytest.mark.asyncio
async def test_health_endpoints(client: AsyncClient):
    """Verifies that health check endpoints respond with 200 OK."""
    res1 = await client.get("/health")
    assert res1.status_code == 200
    assert res1.json()["status"] == "healthy"

    res2 = await client.get("/api/v1/health")
    assert res2.status_code == 200
    assert res2.json()["database"] == "connected"


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    """Verifies that protected routes reject requests missing an Authorization header."""
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "error" in res.json()
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_invalid_token_rejected(client: AsyncClient):
    """Verifies that tampered or malformed tokens are rejected with 401."""
    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_expired_token_rejected(client: AsyncClient, make_jwt):
    """Verifies that expired tokens are strictly rejected with 401."""
    expired_token = make_jwt(
        user_id=str(uuid.uuid4()),
        email="expired@brand.in",
        expires_in=-300,  # Expired 5 minutes ago
    )
    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert "expired" in res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_token_auto_provisions_user(client: AsyncClient, make_jwt):
    """Verifies that a valid Supabase JWT creates the user profile upon first access."""
    user_id = str(uuid.uuid4())
    email = "ananya.deshmukh@auraterra.in"
    token = make_jwt(user_id=user_id, email=email)

    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["id"] == user_id
    assert data["user"]["email"] == email
    assert data["user"]["is_platform_admin"] is False
    assert data["organizations"] == []


@pytest.mark.asyncio
async def test_sync_profile_updates_metadata(client: AsyncClient, make_jwt):
    """Verifies updating user profile metadata."""
    user_id = str(uuid.uuid4())
    token = make_jwt(user_id=user_id, email="founder@auraterra.in")

    # Sync updated profile
    res = await client.post(
        "/api/v1/auth/sync-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Ananya Deshmukh",
            "avatar_url": "https://example.com/ananya.png",
        },
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["full_name"] == "Ananya Deshmukh"
    assert updated["avatar_url"] == "https://example.com/ananya.png"


@pytest.mark.asyncio
async def test_token_encryption_at_rest():
    """Verifies AES-256-GCM encryption and decryption roundtrip for external tokens."""
    sensitive_token = "shpat_live_oauth_token_secret_998877"
    encrypted = encrypt_token(sensitive_token)
    assert encrypted != sensitive_token
    assert len(encrypted) > len(sensitive_token)

    decrypted = decrypt_token(encrypted)
    assert decrypted == sensitive_token


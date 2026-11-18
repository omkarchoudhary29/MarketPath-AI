import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ordinary_seller_blocked_from_platform_admin(client: AsyncClient, make_jwt):
    """Ordinary sellers cannot access internal platform administrative routes."""
    seller_id = str(uuid.uuid4())
    seller_token = make_jwt(
        user_id=seller_id,
        email="seller@auraterra.in",
        is_platform_admin=False,
    )

    # Attempt to access platform overview
    res1 = await client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {seller_token}"},
    )
    assert res1.status_code == 403
    assert "Platform Administrator" in res1.json()["error"]["message"]

    # Attempt to list all platform organizations
    res2 = await client.get(
        "/api/v1/admin/organizations",
        headers={"Authorization": f"Bearer {seller_token}"},
    )
    assert res2.status_code == 403

    # Attempt to view platform audit logs
    res3 = await client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {seller_token}"},
    )
    assert res3.status_code == 403


@pytest.mark.asyncio
async def test_platform_admin_can_access_global_telemetry(client: AsyncClient, make_jwt):
    """Internal platform operator can query telemetry across tenants."""
    admin_id = str(uuid.uuid4())
    admin_token = make_jwt(
        user_id=admin_id,
        email="ops@marketpath.ai",
        is_platform_admin=True,
    )

    # 1. Admin overview
    overview_res = await client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert overview_res.status_code == 200
    telemetry = overview_res.json()["telemetry"]
    assert "total_organizations" in telemetry
    assert "total_users" in telemetry
    assert telemetry["operator_email"] == "ops@marketpath.ai"

    # 2. Admin organization search
    orgs_res = await client.get(
        "/api/v1/admin/organizations",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert orgs_res.status_code == 200
    assert isinstance(orgs_res.json(), list)

    # 3. Global audit logs
    logs_res = await client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert logs_res.status_code == 200
    assert isinstance(logs_res.json(), list)


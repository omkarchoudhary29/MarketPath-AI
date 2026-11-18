import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_missing_organization_header(client: AsyncClient, make_jwt):
    """Verifies that tenant-scoped routes reject requests lacking X-Organization-Id."""
    token = make_jwt(user_id=str(uuid.uuid4()), email="seller@brand.in")
    res = await client.get(
        "/api/v1/organizations/active",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "X-Organization-Id" in res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_invalid_organization_header_format(client: AsyncClient, make_jwt):
    """Verifies that non-UUID organization headers are rejected."""
    token = make_jwt(user_id=str(uuid.uuid4()), email="seller@brand.in")
    res = await client.get(
        "/api/v1/organizations/active",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Organization-Id": "not-a-valid-uuid",
        },
    )
    assert res.status_code == 400
    assert "valid UUID" in res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_organization_onboarding_and_brand_initialization(client: AsyncClient, make_jwt):
    """Verifies that creating an organization sets the creator as owner and creates default brand profile."""
    user_id = str(uuid.uuid4())
    token = make_jwt(user_id=user_id, email="ananya@auraterra.in")

    create_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Aura Terra Living",
            "brand_name": "Aura Terra Living",
            "category": "Home & Living",
            "currency": "INR",
        },
    )
    assert create_res.status_code == 201
    org = create_res.json()
    assert org["name"] == "Aura Terra Living"
    assert org["slug"] == "aura-terra-living"
    assert org["role"] == "owner"
    org_id = org["id"]

    # Verify active organization can be fetched with X-Organization-Id
    active_res = await client.get(
        "/api/v1/organizations/active",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Organization-Id": org_id,
        },
    )
    assert active_res.status_code == 200
    assert active_res.json()["id"] == org_id

    # Verify brand profile was automatically initialized
    brand_res = await client.get(
        "/api/v1/brand-profile",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Organization-Id": org_id,
        },
    )
    assert brand_res.status_code == 200
    brand = brand_res.json()
    assert brand["brand_name"] == "Aura Terra Living"
    assert brand["organization_id"] == org_id
    assert brand["tone_of_voice"] == "Warm & Aesthetic"


@pytest.mark.asyncio
async def test_cross_tenant_access_strictly_prevented(client: AsyncClient, make_jwt):
    """Critical: User A in Org A cannot access or mutate Org B's resources."""
    user_a_id = str(uuid.uuid4())
    token_a = make_jwt(user_id=user_a_id, email="seller_a@brand-a.in")

    user_b_id = str(uuid.uuid4())
    token_b = make_jwt(user_id=user_b_id, email="seller_b@brand-b.in")

    # User A creates Org A
    res_a = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "Brand Alpha Studios", "category": "Home & Living"},
    )
    assert res_a.status_code == 201
    org_a_id = res_a.json()["id"]

    # User B creates Org B
    res_b = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"name": "Brand Beta Ceramics", "category": "Kitchen & Dining"},
    )
    assert res_b.status_code == 201
    org_b_id = res_b.json()["id"]

    # ATTACK 1: User A attempts to read Org B's active organization details
    attack1 = await client.get(
        "/api/v1/organizations/active",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Organization-Id": org_b_id,
        },
    )
    assert attack1.status_code == 403
    assert attack1.json()["error"]["code"] == "FORBIDDEN"
    assert "not a member" in attack1.json()["error"]["message"]

    # ATTACK 2: User A attempts to read Org B's brand profile
    attack2 = await client.get(
        "/api/v1/brand-profile",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Organization-Id": org_b_id,
        },
    )
    assert attack2.status_code == 403
    assert attack2.json()["error"]["code"] == "FORBIDDEN"

    # ATTACK 3: User A attempts to update Org B's settings
    attack3 = await client.patch(
        "/api/v1/organizations/active",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Organization-Id": org_b_id,
        },
        json={"name": "Hacked Brand Name"},
    )
    assert attack3.status_code == 403

    # ATTACK 4: User B attempts to view Org A's team members
    attack4 = await client.get(
        "/api/v1/team/members",
        headers={
            "Authorization": f"Bearer {token_b}",
            "X-Organization-Id": org_a_id,
        },
    )
    assert attack4.status_code == 403


@pytest.mark.asyncio
async def test_tenant_isolation_in_organization_listing(client: AsyncClient, make_jwt):
    """Verifies that listing organizations only returns organizations where the user has a membership."""
    user_a_id = str(uuid.uuid4())
    token_a = make_jwt(user_id=user_a_id, email="user_a@test.in")

    user_b_id = str(uuid.uuid4())
    token_b = make_jwt(user_id=user_b_id, email="user_b@test.in")

    # User A creates Org 1 and Org 2
    await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "User A First Store"},
    )
    await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "User A Second Store"},
    )

    # User B creates Org 3
    await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"name": "User B Store"},
    )

    # User A listing orgs must see exactly 2 orgs
    list_a = await client.get(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert list_a.status_code == 200
    assert len(list_a.json()) == 2
    org_names_a = [o["name"] for o in list_a.json()]
    assert "User A First Store" in org_names_a
    assert "User A Second Store" in org_names_a
    assert "User B Store" not in org_names_a

    # User B listing orgs must see exactly 1 org
    list_b = await client.get(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert list_b.status_code == 200
    assert len(list_b.json()) == 1
    assert list_b.json()[0]["name"] == "User B Store"


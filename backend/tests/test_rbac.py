import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rbac_roles_hierarchy(client: AsyncClient, make_jwt):
    """Verifies that role permissions (Owner, Admin, Marketer, Viewer) are strictly enforced."""
    # 1. Owner sets up organization
    owner_id = str(uuid.uuid4())
    owner_token = make_jwt(user_id=owner_id, email="owner@auraterra.in")

    org_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Aura Living Org", "category": "Home & Living"},
    )
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]

    # 2. Owner invites a Marketer and a Viewer
    marketer_email = "marketer@auraterra.in"
    inv_marketer = await client.post(
        "/api/v1/team/invites",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Organization-Id": org_id,
        },
        json={"email": marketer_email, "role": "marketer", "full_name": "Rohan Marketer"},
    )
    assert inv_marketer.status_code == 201
    marketer_user_id = str(inv_marketer.json()["user_id"])
    marketer_member_id = str(inv_marketer.json()["id"])

    viewer_email = "viewer@auraterra.in"
    inv_viewer = await client.post(
        "/api/v1/team/invites",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Organization-Id": org_id,
        },
        json={"email": viewer_email, "role": "viewer", "full_name": "Kavita Viewer"},
    )
    assert inv_viewer.status_code == 201
    viewer_user_id = str(inv_viewer.json()["user_id"])

    marketer_token = make_jwt(user_id=marketer_user_id, email=marketer_email)
    viewer_token = make_jwt(user_id=viewer_user_id, email=viewer_email)

    # 3. VIEWER TESTS
    # Viewer can read active org details
    v_read = await client.get(
        "/api/v1/organizations/active",
        headers={"Authorization": f"Bearer {viewer_token}", "X-Organization-Id": org_id},
    )
    assert v_read.status_code == 200
    assert v_read.json()["role"] == "viewer"

    # Viewer CANNOT update organization name (Forbidden)
    v_patch = await client.patch(
        "/api/v1/organizations/active",
        headers={"Authorization": f"Bearer {viewer_token}", "X-Organization-Id": org_id},
        json={"name": "Viewer Unauthorized Name"},
    )
    assert v_patch.status_code == 403
    assert "Permission denied" in v_patch.json()["error"]["message"]

    # Viewer CANNOT update brand profile (Forbidden)
    v_brand_update = await client.put(
        "/api/v1/brand-profile",
        headers={"Authorization": f"Bearer {viewer_token}", "X-Organization-Id": org_id},
        json={"tone_of_voice": "Edgy & Disruptive"},
    )
    assert v_brand_update.status_code == 403

    # Viewer CANNOT invite members (Forbidden)
    v_invite = await client.post(
        "/api/v1/team/invites",
        headers={"Authorization": f"Bearer {viewer_token}", "X-Organization-Id": org_id},
        json={"email": "newbie@auraterra.in", "role": "viewer"},
    )
    assert v_invite.status_code == 403

    # 4. MARKETER TESTS
    # Marketer can read brand profile
    m_brand_read = await client.get(
        "/api/v1/brand-profile",
        headers={"Authorization": f"Bearer {marketer_token}", "X-Organization-Id": org_id},
    )
    assert m_brand_read.status_code == 200

    # Marketer CANNOT invite other team members (requires Admin/Owner)
    m_invite = await client.post(
        "/api/v1/team/invites",
        headers={"Authorization": f"Bearer {marketer_token}", "X-Organization-Id": org_id},
        json={"email": "guest@auraterra.in", "role": "viewer"},
    )
    assert m_invite.status_code == 403

    # Marketer CANNOT delete a team member (requires Owner)
    m_delete = await client.delete(
        f"/api/v1/team/members/{marketer_member_id}",
        headers={"Authorization": f"Bearer {marketer_token}", "X-Organization-Id": org_id},
    )
    assert m_delete.status_code == 403

    # 5. OWNER REMOVAL TESTS
    # Owner removes marketer -> Success 204
    owner_delete = await client.delete(
        f"/api/v1/team/members/{marketer_member_id}",
        headers={"Authorization": f"Bearer {owner_token}", "X-Organization-Id": org_id},
    )
    assert owner_delete.status_code == 204

    # Removed marketer can no longer access the organization -> 403
    m_after_delete = await client.get(
        "/api/v1/organizations/active",
        headers={"Authorization": f"Bearer {marketer_token}", "X-Organization-Id": org_id},
    )
    assert m_after_delete.status_code == 403


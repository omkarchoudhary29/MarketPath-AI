import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sign_upload_endpoint(client: AsyncClient, make_jwt):
    """Verifies generating signed Cloudinary direct-upload parameters."""
    token = make_jwt(user_id=str(uuid.uuid4()), email="marketer@auraterra.in")

    org_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Media Test Store"},
    )
    org_id = org_res.json()["id"]

    res = await client.post(
        "/api/v1/media/sign-upload",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={"folder": "products", "resource_type": "image"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "signature" in data
    assert "timestamp" in data
    assert "api_key" in data
    assert f"marketpath/{org_id}/products" in data["folder"]
    assert "upload_url" in data


@pytest.mark.asyncio
async def test_attach_and_reorder_product_media(client: AsyncClient, make_jwt):
    """Verifies attaching media, reordering display order, and deleting media."""
    token = make_jwt(user_id=str(uuid.uuid4()), email="owner@auraterra.in")

    org_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Gallery Store"},
    )
    org_id = org_res.json()["id"]

    prod_res = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={"sku": "GALLERY-01", "title": "Ceramic Vase", "category": "Home & Living", "base_price": 1200.0},
    )
    prod_id = prod_res.json()["id"]

    # 1. Attach 2 media images
    m1_res = await client.post(
        f"/api/v1/products/{prod_id}/media",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "cloudinary_public_id": "marketpath/vase_front",
            "media_url": "https://res.cloudinary.com/demo/image/upload/vase_front.jpg",
            "media_type": "image",
            "alt_text": "Vase front view",
            "display_order": 0,
        },
    )
    assert m1_res.status_code == 201
    m1_id = m1_res.json()["id"]

    m2_res = await client.post(
        f"/api/v1/products/{prod_id}/media",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "cloudinary_public_id": "marketpath/vase_detail",
            "media_url": "https://res.cloudinary.com/demo/image/upload/vase_detail.jpg",
            "media_type": "image",
            "alt_text": "Texture detail",
            "display_order": 1,
        },
    )
    assert m2_res.status_code == 201
    m2_id = m2_res.json()["id"]

    # 2. Reorder media: make m2 first (order 0) and m1 second (order 1)
    reorder_res = await client.patch(
        f"/api/v1/products/{prod_id}/media/reorder",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "items": [
                {"media_id": m2_id, "display_order": 0},
                {"media_id": m1_id, "display_order": 1},
            ]
        },
    )
    assert reorder_res.status_code == 200
    reordered_items = reorder_res.json()
    assert reordered_items[0]["id"] == m2_id
    assert reordered_items[1]["id"] == m1_id

    # 3. Delete m1
    del_res = await client.delete(
        f"/api/v1/products/{prod_id}/media/{m1_id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
    )
    assert del_res.status_code == 204

    # Verify only m2 remains
    prod_check = await client.get(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
    )
    assert len(prod_check.json()["media"]) == 1
    assert prod_check.json()["media"][0]["id"] == m2_id


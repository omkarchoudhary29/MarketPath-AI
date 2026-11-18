import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_ai_shopify_copy(client: AsyncClient, make_jwt):
    """Verifies generating structured, grounded Shopify product copy."""
    token = make_jwt(user_id=str(uuid.uuid4()), email="marketer@auraterra.in")

    org_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Aura Terra Living", "category": "Home & Living"},
    )
    org_id = org_res.json()["id"]

    prod_res = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "sku": "CER-BOWL-01",
            "title": "Stoneware Salad Bowl",
            "category": "Kitchen & Dining",
            "base_price": 1499.0,
            "materials": ["Earthy Terracotta", "Food-safe White Glaze"],
            "dimensions": {"length": 25, "width": 25, "height": 9, "unit": "cm"},
        },
    )
    prod_id = prod_res.json()["id"]

    # Generate Shopify copy
    ai_res = await client.post(
        "/api/v1/ai-studio/generate",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "product_id": prod_id,
            "content_type": "shopify_copy",
            "target_channel": "shopify",
            "tone_override": "Warm & Aesthetic",
        },
    )
    assert ai_res.status_code == 201
    ai_data = ai_res.json()
    assert ai_data["content_type"] == "shopify_copy"
    assert ai_data["version_number"] == 1
    assert "payload" in ai_data
    payload = ai_data["payload"]
    assert "title" in payload
    assert "body_html" in payload
    assert "bullet_points" in payload
    assert "meta_title" in payload
    assert "meta_description" in payload
    assert "grounded_facts" in payload
    assert any("CER-BOWL-01" in fact or "1499" in fact for fact in payload["grounded_facts"])


@pytest.mark.asyncio
async def test_generate_ai_instagram_and_ad_hooks(client: AsyncClient, make_jwt):
    """Verifies generating Instagram posts and Ad hooks with structured schemas."""
    token = make_jwt(user_id=str(uuid.uuid4()), email="marketer@auraterra.in")

    org_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Studio Gifting"},
    )
    org_id = org_res.json()["id"]

    prod_res = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "sku": "GIFT-BOX-01",
            "title": "Artisanal Brass Coffee Filter Gift Box",
            "category": "Artisanal Gifting",
            "base_price": 2499.0,
            "materials": ["Pure Brass", "Handmade Pine Wood Box"],
        },
    )
    prod_id = prod_res.json()["id"]

    # 1. Instagram Post
    ig_res = await client.post(
        "/api/v1/ai-studio/generate",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "product_id": prod_id,
            "content_type": "instagram_post",
            "target_channel": "instagram",
        },
    )
    assert ig_res.status_code == 201
    ig_data = ig_res.json()["payload"]
    assert "hook" in ig_data
    assert "caption" in ig_data
    assert "hashtags" in ig_data
    assert isinstance(ig_data["carousel_slides"], list)

    # 2. Ad Hooks
    ad_res = await client.post(
        "/api/v1/ai-studio/generate",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "product_id": prod_id,
            "content_type": "ad_hook",
            "target_channel": "meta_ads",
            "campaign_objective": "Festive Gifting",
        },
    )
    assert ad_res.status_code == 201
    ad_data = ad_res.json()["payload"]
    assert len(ad_data["headlines"]) > 0
    assert len(ad_data["primary_texts"]) > 0
    assert "audience_angle" in ad_data


@pytest.mark.asyncio
async def test_content_lifecycle_regeneration_edit_and_approval(client: AsyncClient, make_jwt):
    """Verifies complete version lifecycle: initial generation, regeneration (v2), manual edit, and approval sync."""
    user_id = str(uuid.uuid4())
    token = make_jwt(user_id=user_id, email="marketer@auraterra.in")

    org_res = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Lifecycle Store"},
    )
    org_id = org_res.json()["id"]

    prod_res = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={"sku": "LIFECYCLE-01", "title": "Bamboo Table Runner", "category": "Home & Living", "base_price": 750.0},
    )
    prod_id = prod_res.json()["id"]

    # 1. Initial Generation (v1)
    gen_res = await client.post(
        "/api/v1/ai-studio/generate",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "product_id": prod_id,
            "content_type": "shopify_copy",
            "target_channel": "shopify",
        },
    )
    gen_data = gen_res.json()
    generation_id = gen_data["generation_id"]
    v1_id = gen_data["version_id"]
    assert gen_data["version_number"] == 1

    # 2. Regenerate (v2) with revised instruction
    regen_res = await client.post(
        "/api/v1/ai-studio/regenerate",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "generation_id": generation_id,
            "revised_instructions": "Make it more minimal and focus on eco-friendly dining.",
            "tone_override": "Minimal & Contemporary",
        },
    )
    assert regen_res.status_code == 200
    v2_data = regen_res.json()
    assert v2_data["version_number"] == 2
    v2_id = v2_data["version_id"]

    # 3. Manual Edit of v2
    custom_edit = dict(v2_data["payload"])
    custom_edit["title"] = "Refined Artisanal Bamboo Runner | Eco Living"
    edit_res = await client.patch(
        f"/api/v1/ai-studio/versions/{v2_id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={"edited_payload": custom_edit},
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["edited_payload"]["title"] == "Refined Artisanal Bamboo Runner | Eco Living"

    # 4. Approve Version 2 and Sync to Channel Override
    approve_res = await client.post(
        "/api/v1/ai-studio/approve-version",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={
            "version_id": v2_id,
            "apply_to_channel_override": True,
        },
    )
    assert approve_res.status_code == 200
    approved_ver = approve_res.json()
    assert approved_ver["is_approved"] is True
    assert approved_ver["approved_by_user_id"] == user_id
    assert approved_ver["approved_at"] is not None

    # 5. Verify Channel Override was updated
    overrides_res = await client.get(
        f"/api/v1/products/{prod_id}/overrides",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
    )
    assert overrides_res.status_code == 200
    overrides = overrides_res.json()
    assert len(overrides) == 1
    assert overrides[0]["channel_type"] == "shopify"
    assert overrides[0]["custom_title"] == "Refined Artisanal Bamboo Runner | Eco Living"
    assert overrides[0]["is_approved_for_channel"] is True

    # 6. Verify Generation History list
    history_res = await client.get(
        f"/api/v1/ai-studio/history/{prod_id}",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 1
    assert len(history[0]["versions"]) == 2


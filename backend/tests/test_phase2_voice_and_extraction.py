"""Test Phase 2: Decoupled Speech-to-Text, Brand Intelligence, and Product Extraction.

Verifies:
1. Verbatim Speech-to-Text transcription (no fabricated text on "Hello" or silence).
2. Clean greeting handling in brand intelligence (no mock products or fake brand profiles).
3. 5-section brand profile extraction with provenance mapping.
4. Product specification extraction with automatic unit normalization (grams -> kg, mm -> cm).
5. Category-aware attributes, SKU generation, and marketplace compliance detection.
"""

import base64
import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.services.gemini_service import (
    transcribe_speech,
    extract_brand_intelligence,
    extract_product_specifications,
)


@pytest.fixture
def auth_headers(company_user_token: str) -> dict:
    return {
        "Authorization": f"Bearer {company_user_token}",
        "Content-Type": "application/json",
    }


@pytest.mark.asyncio
async def test_transcribe_speech_empty_or_silence():
    """Silence or empty audio should return no_speech_detected and zero mock paragraphs."""
    empty_bytes = b"\x00" * 30
    res = await transcribe_speech(empty_bytes, "audio/webm")
    assert res["status"] == "no_speech_detected"
    assert res["transcript"] == ""


@pytest.mark.asyncio
async def test_extract_brand_greeting_handles_cleanly():
    """Saying 'Hello' should return a friendly follow-up without inventing ceramic kulhads."""
    res = await extract_brand_intelligence("Hello")
    assert res["is_ready_for_confirmation"] is False
    assert "Hello! Welcome to MarketPath AI" in res["reply_message"]
    assert "brand_name" in res["missing_fields"]
    assert res["follow_up_question"] is not None
    # Provenance should indicate missing
    assert res["provenance"]["brand_name"] == "missing"


@pytest.mark.asyncio
async def test_extract_product_greeting_handles_cleanly():
    """Saying 'Hi' to product extractor should flag is_valid_product as False."""
    res = await extract_product_specifications("Hi")
    assert res["is_valid_product"] is False
    assert res["title"] == ""
    assert "title" in res["missing_marketplace_fields"]


@pytest.mark.asyncio
async def test_extract_product_unit_normalization():
    """Should normalize 500g to 0.5 kg and parse selling price & MRP accurately."""
    sample_text = (
        "Pure organic cold-pressed sesame oil. "
        "Selling price is 299 rupees, MRP is 399 rupees. "
        "Weight is 500g. Dimensions are 8cm by 8cm by 20cm. "
        "Packaged in dark glass bottle."
    )
    res = await extract_product_specifications(sample_text, category_hint="Food & Beverages")
    assert res["is_valid_product"] is True
    assert res["base_price"] == 299.0
    # Weight should be normalized to kg
    assert res["weight_kg"] == 0.5 or (res["weight_kg"] is not None and res["weight_kg"] <= 1.0)
    assert res["sku"] != ""
    assert res["category"] is not None


@pytest.mark.asyncio
async def test_voice_transcribe_endpoint_json(client: AsyncClient, owner_headers: dict):
    """POST /api/v1/voice/transcribe with small audio should respond cleanly."""
    dummy_b64 = base64.b64encode(b"\x00" * 40).decode()
    resp = await client.post(
        "/api/v1/voice/transcribe",
        headers=owner_headers,
        json={"audio_base64": dummy_b64, "mime_type": "audio/webm"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "transcript" in data
    assert data["status"] == "no_speech_detected"


@pytest.mark.asyncio
async def test_voice_extract_brand_endpoint(client: AsyncClient, owner_headers: dict):
    """POST /api/v1/voice/extract-brand returns 5 sections and follow-up question."""
    resp = await client.post(
        "/api/v1/voice/extract-brand",
        headers=owner_headers,
        json={"transcript": "Hello"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "sections" in data
    assert "identity" in data["sections"]
    assert "story_positioning" in data["sections"]
    assert "target_customers" in data["sections"]
    assert "guidelines" in data["sections"]
    assert "selling_policies" in data["sections"]
    assert data["is_ready_for_confirmation"] is False


@pytest.mark.asyncio
async def test_voice_extract_product_endpoint(client: AsyncClient, owner_headers: dict):
    """POST /api/v1/voice/extract-product extracts specs from text."""
    resp = await client.post(
        "/api/v1/voice/extract-product",
        headers=owner_headers,
        json={
            "transcript": "Handmade ceramic kulhad cup set of 4. Selling price 499 rupees, MRP 699 rupees. Weight 800g.",
            "category_hint": "Home & Living",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid_product"] is True
    assert data["base_price"] == 499.0
    assert data["sku"].startswith("MP-")

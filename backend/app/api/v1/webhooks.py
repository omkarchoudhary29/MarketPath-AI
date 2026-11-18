"""Inbound Webhook API Endpoints.

Handles external webhooks from Shopify and Meta with HMAC cryptographic signature validation
and event deduplication via the webhook_events table.
"""

import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.schemas.publishing import WebhookIngestResponse
from backend.app.services.webhook_service import WebhookService

router = APIRouter()


@router.post("/shopify", response_model=WebhookIngestResponse)
async def shopify_webhook(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None, alias="X-Shopify-Hmac-Sha256"),
    x_shopify_webhook_id: Optional[str] = Header(None, alias="X-Shopify-Webhook-Id"),
    x_shopify_topic: Optional[str] = Header(None, alias="X-Shopify-Topic"),
    db: AsyncSession = Depends(get_db),
):
    """Ingests Shopify webhooks (e.g. inventory levels, product updates) with HMAC verification."""
    raw_body = await request.body()

    if not WebhookService.verify_shopify_hmac(raw_body, x_shopify_hmac_sha256):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Shopify HMAC signature verification failed.",
        )

    event_id = x_shopify_webhook_id or str(uuid.uuid4())
    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        payload = {"raw": raw_body.decode("utf-8", errors="replace")}

    is_new, msg = await WebhookService.process_inbound_event(
        session=db,
        source="shopify",
        event_id=event_id,
        payload=payload,
    )

    return WebhookIngestResponse(
        status="ok",
        event_id=event_id,
        source="shopify",
        processed=is_new,
        message=msg,
    )


@router.get("/meta")
async def meta_webhook_verification(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
):
    """Meta webhook verification endpoint (handles Meta subscription handshake)."""
    # Verify token configured in settings or default
    expected_token = getattr(settings, "META_WEBHOOK_VERIFY_TOKEN", settings.SECRET_KEY)
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return Response(content=hub_challenge or "", media_type="text/plain")

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch.",
    )


@router.post("/meta", response_model=WebhookIngestResponse)
async def meta_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db: AsyncSession = Depends(get_db),
):
    """Ingests Meta/Instagram webhooks with X-Hub-Signature-256 verification."""
    raw_body = await request.body()

    if not WebhookService.verify_meta_signature(raw_body, x_hub_signature_256):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Meta X-Hub-Signature-256 verification failed.",
        )

    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        payload = {"raw": raw_body.decode("utf-8", errors="replace")}

    # Extract event ID or generate unique hash
    event_id = str(uuid.uuid4())
    if "entry" in payload and isinstance(payload["entry"], list) and len(payload["entry"]) > 0:
        event_id = str(payload["entry"][0].get("id", event_id))

    is_new, msg = await WebhookService.process_inbound_event(
        session=db,
        source="meta",
        event_id=event_id,
        payload=payload,
    )

    return WebhookIngestResponse(
        status="ok",
        event_id=event_id,
        source="meta",
        processed=is_new,
        message=msg,
    )


@router.post("/razorpay", response_model=WebhookIngestResponse)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """Ingests Razorpay payment webhooks with cryptographic HMAC signature verification."""
    raw_body = await request.body()
    from backend.app.services.payment_service import PaymentService
    gateway = PaymentService.get_gateway("razorpay")

    if not gateway.verify_webhook_signature(raw_body, x_razorpay_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Razorpay webhook signature verification failed.",
        )

    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        payload = {"raw": raw_body.decode("utf-8", errors="replace")}

    event_id = payload.get("event_id") or payload.get("id") or str(uuid.uuid4())
    is_new, msg = await WebhookService.process_inbound_event(
        session=db,
        source="razorpay",
        event_id=event_id,
        payload=payload,
    )

    return WebhookIngestResponse(
        status="ok",
        event_id=event_id,
        source="razorpay",
        processed=is_new,
        message=msg,
    )


@router.post("/cashfree", response_model=WebhookIngestResponse)
async def cashfree_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None, alias="x-webhook-signature"),
    db: AsyncSession = Depends(get_db),
):
    """Ingests Cashfree payment webhooks with cryptographic signature verification."""
    raw_body = await request.body()
    from backend.app.services.payment_service import PaymentService
    gateway = PaymentService.get_gateway("cashfree")

    if not gateway.verify_webhook_signature(raw_body, x_webhook_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cashfree webhook signature verification failed.",
        )

    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        payload = {"raw": raw_body.decode("utf-8", errors="replace")}

    event_id = payload.get("event_id") or payload.get("data", {}).get("order", {}).get("order_id") or str(uuid.uuid4())
    is_new, msg = await WebhookService.process_inbound_event(
        session=db,
        source="cashfree",
        event_id=event_id,
        payload=payload,
    )

    return WebhookIngestResponse(
        status="ok",
        event_id=event_id,
        source="cashfree",
        processed=is_new,
        message=msg,
    )


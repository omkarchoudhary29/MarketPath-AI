"""Webhook Ingestion and Verification Service.

Handles cryptographic signature verification (Shopify HMAC, Meta X-Hub-Signature),
deduplication via webhook_events, and event processing.
"""

import base64
import hashlib
import hmac
import json
import logging
import uuid
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.channel import WebhookEvent

logger = logging.getLogger(__name__)


class WebhookVerificationError(Exception):
    """Raised when webhook signature verification fails."""
    pass


class WebhookService:
    """Verifies and processes inbound webhook payloads."""

    @staticmethod
    def verify_shopify_hmac(raw_body: bytes, hmac_header: Optional[str]) -> bool:
        """Verifies Shopify X-Shopify-Hmac-Sha256 header using SHOPIFY_API_SECRET."""
        if not hmac_header or not settings.SHOPIFY_API_SECRET:
            return False

        calculated_hmac = base64.b64encode(
            hmac.new(
                settings.SHOPIFY_API_SECRET.encode("utf-8"),
                raw_body,
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        return hmac.compare_digest(calculated_hmac, hmac_header)

    @staticmethod
    def verify_meta_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
        """Verifies Meta X-Hub-Signature-256 header using META_APP_SECRET."""
        if not signature_header or not settings.META_APP_SECRET:
            return False

        if not signature_header.startswith("sha256="):
            return False

        expected_sig = signature_header[7:]
        calculated_sig = hmac.new(
            settings.META_APP_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(calculated_sig, expected_sig)

    @classmethod
    async def process_inbound_event(
        cls,
        session: AsyncSession,
        source: str,
        event_id: str,
        payload: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """Deduplicates and stores an inbound webhook event.
        
        Returns:
            (is_new_event, message)
        """
        # Deduplication check
        stmt = select(WebhookEvent).where(
            WebhookEvent.source == source,
            WebhookEvent.event_id == event_id,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"Duplicate webhook received for {source} event {event_id}. Skipping.")
            return False, "Duplicate event previously processed."

        # Insert record
        event_record = WebhookEvent(
            source=source,
            event_id=event_id,
            payload=payload,
            status="processed",
        )
        session.add(event_record)
        await session.commit()

        logger.info(f"Successfully ingested and recorded webhook {source}:{event_id}")
        return True, "Event successfully recorded."


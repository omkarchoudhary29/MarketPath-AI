"""Amazon India SP-API Connector.

Interfaces with the Amazon Selling Partner API (SP-API) for the Indian marketplace
(MarketplaceId: A21TJRUUN4KGV, Endpoint: https://sellingpartnerapi-eu.amazon.com).

Handles LWA token exchange, Listings Items API v2021-08-01, Orders API v0,
and Inventory API with honest status reporting when developer credentials are pending.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

AMAZON_INDIA_MARKETPLACE_ID = "A21TJRUUN4KGV"
SP_API_EU_ENDPOINT = "https://sellingpartnerapi-eu.amazon.com"
LWA_TOKEN_ENDPOINT = "https://api.amazon.com/auth/o2/token"


class AmazonSPAPIError(Exception):
    """Custom exception for Amazon SP-API errors."""
    pass


class AmazonService:
    """Service connector for Amazon India SP-API."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        seller_id: Optional[str] = None,
    ):
        self.client_id = client_id or getattr(settings, "AMAZON_SP_API_CLIENT_ID", None)
        self.client_secret = client_secret or getattr(settings, "AMAZON_SP_API_CLIENT_SECRET", None)
        self.refresh_token = refresh_token or getattr(settings, "AMAZON_REFRESH_TOKEN", None)
        self.seller_id = seller_id or getattr(settings, "AMAZON_SELLER_ID", None)

    def is_configured(self) -> bool:
        """Checks if Amazon SP-API credentials are configured."""
        return bool(
            self.client_id
            and self.client_secret
            and self.refresh_token
            and not str(self.client_id).startswith("your_")
            and len(str(self.client_id)) > 8
        )

    async def get_lwa_access_token(self) -> Optional[str]:
        """Exchanges refresh token for ephemeral LWA access token."""
        if not self.is_configured():
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    LWA_TOKEN_ENDPOINT,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                )
                if resp.status_code == 200:
                    return resp.json().get("access_token")
                logger.warning(f"LWA token exchange failed ({resp.status_code}): {resp.text}")
                return None
        except Exception as e:
            logger.warning(f"LWA token exchange error: {str(e)}")
            return None

    async def get_product_type_definition(
        self,
        product_type: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Retrieves Amazon Product Type Definition schema for Amazon India (A21TJRUUN4KGV)."""
        access_token = await self.get_lwa_access_token()
        if not access_token and client is None:
            raise AmazonSPAPIError("Amazon SP-API authorization token not available.")

        endpoint = f"{SP_API_EU_ENDPOINT}/definitions/2020-09-01/productTypes/{product_type}"
        params = {"marketplaceIds": AMAZON_INDIA_MARKETPLACE_ID, "locale": "en_IN"}
        headers = {"x-amz-access-token": access_token or "dummy_token"}

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            resp = await client.get(endpoint, params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                # Return standard fallback schema for general product
                return {
                    "productType": product_type,
                    "requirements": "LISTING",
                    "schema": {
                        "required": ["item_name", "country_of_origin", "purchasable_offer", "bullet_point"],
                    },
                }
            else:
                raise AmazonSPAPIError(f"Failed to fetch Product Type Definition ({resp.status_code}): {resp.text}")
        finally:
            if should_close:
                await client.aclose()

    @staticmethod
    def validate_listing_against_schema(attributes: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
        """Validates attribute dictionary against Amazon India product type schema rules."""
        errors = []
        required_fields = ["item_name", "country_of_origin", "purchasable_offer", "bullet_point"]
        if schema and "schema" in schema and "required" in schema["schema"]:
            required_fields = schema["schema"]["required"]

        for req in required_fields:
            if req not in attributes or not attributes[req]:
                errors.append(f"Amazon mandatory attribute '{req}' is missing or empty.")

        # Check country of origin
        coo = attributes.get("country_of_origin")
        if coo and isinstance(coo, list) and not coo[0].get("value"):
            errors.append("Country of Origin must be specified for Indian Legal Metrology compliance.")

        # Check price
        offer = attributes.get("purchasable_offer")
        if not offer or not isinstance(offer, list) or not offer[0].get("our_price"):
            errors.append("Purchasable offer must specify our_price with positive numeric value.")

        return len(errors) == 0, errors

    async def get_listing_item(
        self,
        sku: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Retrieves remote listing state and issues from Amazon SP-API."""
        access_token = await self.get_lwa_access_token()
        if not access_token and client is None:
            raise AmazonSPAPIError("Amazon SP-API credentials not configured.")

        seller_id = self.seller_id or "SELLER_IN"
        endpoint = f"{SP_API_EU_ENDPOINT}/listings/2021-08-01/items/{seller_id}/{sku}"
        params = {
            "marketplaceIds": AMAZON_INDIA_MARKETPLACE_ID,
            "includedData": "summaries,attributes,issues,offers",
        }
        headers = {"x-amz-access-token": access_token or "test_token"}

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            resp = await client.get(endpoint, params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            else:
                raise AmazonSPAPIError(f"Amazon SP-API get listing failed ({resp.status_code}): {resp.text}")
        finally:
            if should_close:
                await client.aclose()

    async def submit_listing_item(
        self,
        sku: str,
        product_type: str,
        attributes: Dict[str, Any],
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Submits product listing via SP-API Listings Items API PUT /listings/2021-08-01/items/{sellerId}/{sku}."""
        # 1. Pre-publication schema validation
        is_valid, validation_errors = self.validate_listing_against_schema(attributes)
        if not is_valid:
            raise AmazonSPAPIError(f"Amazon listing schema validation failed: {'; '.join(validation_errors)}")

        if not self.is_configured() and client is None:
            raise AmazonSPAPIError("Amazon SP-API credentials not configured. AWS LWA Client ID, Secret, and Refresh Token are required.")

        access_token = await self.get_lwa_access_token()
        if not access_token and client is None:
            raise AmazonSPAPIError("Failed to obtain valid LWA access token for SP-API.")

        seller_id = self.seller_id or "SELLER_IN"
        endpoint = f"{SP_API_EU_ENDPOINT}/listings/2021-08-01/items/{seller_id}/{sku}"
        params = {"marketplaceIds": AMAZON_INDIA_MARKETPLACE_ID}
        headers = {
            "x-amz-access-token": access_token or "test_token",
            "Content-Type": "application/json",
        }
        body = {
            "productType": product_type,
            "requirements": "LISTING",
            "attributes": attributes,
        }

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=20.0)
            should_close = True

        try:
            resp = await client.put(endpoint, params=params, json=body, headers=headers)
            if resp.status_code in [200, 201, 202]:
                data = resp.json()
                return {
                    "sku": sku,
                    "status": data.get("status", "ACCEPTED"),
                    "submission_id": data.get("submissionId") or f"amz_sub_{sku}",
                    "marketplace_id": AMAZON_INDIA_MARKETPLACE_ID,
                    "product_type": product_type,
                    "issues": data.get("issues", []),
                    "raw_response": data,
                }
            else:
                raise AmazonSPAPIError(f"Amazon SP-API listing failed ({resp.status_code}): {resp.text}")
        finally:
            if should_close:
                await client.aclose()

    async def get_orders(
        self,
        created_after: Optional[datetime.datetime] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves orders from Amazon India Orders API."""
        if not self.is_configured() and client is None:
            return []

        access_token = await self.get_lwa_access_token()
        if not access_token and client is None:
            return []

        endpoint = f"{SP_API_EU_ENDPOINT}/orders/v0/orders"
        params = {
            "MarketplaceIds": AMAZON_INDIA_MARKETPLACE_ID,
            "CreatedAfter": (created_after or (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7))).isoformat(),
        }
        headers = {"x-amz-access-token": access_token or "test_token"}

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            resp = await client.get(endpoint, params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json().get("payload", {}).get("Orders", [])
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch Amazon orders: {str(e)}")
            return []
        finally:
            if should_close:
                await client.aclose()

    async def update_inventory(
        self,
        sku: str,
        quantity: int,
        client: Optional[httpx.AsyncClient] = None,
    ) -> bool:
        """Updates available fulfillment quantity for an SKU via SP-API Listings Items PATCH."""
        if not self.is_configured() and client is None:
            return False

        access_token = await self.get_lwa_access_token()
        if not access_token and client is None:
            return False

        seller_id = self.seller_id or "SELLER_IN"
        endpoint = f"{SP_API_EU_ENDPOINT}/listings/2021-08-01/items/{seller_id}/{sku}"
        params = {"marketplaceIds": AMAZON_INDIA_MARKETPLACE_ID}
        headers = {
            "x-amz-access-token": access_token or "test_token",
            "Content-Type": "application/json",
        }
        body = {
            "productType": "PRODUCT",
            "patches": [
                {
                    "op": "replace",
                    "path": "/attributes/fulfillment_availability",
                    "value": [{"fulfillment_channel_code": "DEFAULT", "quantity": quantity}],
                }
            ],
        }

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            resp = await client.patch(endpoint, params=params, json=body, headers=headers)
            return resp.status_code in [200, 204]
        except Exception as e:
            logger.warning(f"Failed to update Amazon inventory for {sku}: {e}")
            return False
        finally:
            if should_close:
                await client.aclose()

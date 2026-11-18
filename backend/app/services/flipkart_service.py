"""Flipkart Seller Hub API Connector.

Interfaces with Flipkart Seller Hub APIs for listing creation, inventory updates,
and order synchronisation across the Flipkart Pan-India marketplace.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

FLIPKART_API_BASE_URL = "https://api.flipkart.net/sellers"
FLIPKART_SANDBOX_BASE_URL = "https://sandbox-api.flipkart.net/sellers"


class FlipkartAPIError(Exception):
    """Custom exception for Flipkart Seller API errors."""
    pass


class FlipkartService:
    """Service connector for Flipkart Seller Hub APIs."""

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        sandbox: bool = True,
    ):
        self.app_id = app_id or getattr(settings, "FLIPKART_APP_ID", None)
        self.app_secret = app_secret or getattr(settings, "FLIPKART_APP_SECRET", None)
        self.base_url = FLIPKART_SANDBOX_BASE_URL if sandbox else FLIPKART_API_BASE_URL

    def is_configured(self) -> bool:
        """Checks if Flipkart Seller Hub API credentials are configured."""
        return bool(
            self.app_id
            and self.app_secret
            and not str(self.app_id).startswith("your_")
            and len(str(self.app_id)) > 6
        )

    @staticmethod
    def validate_listing_payload(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates payload against Flipkart Seller Hub listing rules."""
        errors = []
        price_data = payload.get("price", {})
        sp = price_data.get("selling_price", 0.0)
        mrp = price_data.get("mrp", 0.0)

        if sp <= 0:
            errors.append("Flipkart selling price must be greater than zero.")
        if mrp <= 0:
            errors.append("Flipkart Maximum Retail Price (MRP) must be greater than zero.")
        elif sp > mrp:
            errors.append(f"Flipkart selling price ({sp}) cannot exceed MRP ({mrp}).")

        tax_data = payload.get("tax_details", {})
        if not tax_data.get("hsn"):
            errors.append("Flipkart mandates GST HSN code for tax calculation.")

        pkg = payload.get("package_details", {})
        if not pkg.get("weight") or float(pkg.get("weight", 0)) <= 0:
            errors.append("Flipkart requires package shipping dead weight in kg.")

        return len(errors) == 0, errors

    async def get_access_token(self, client: Optional[httpx.AsyncClient] = None) -> Optional[str]:
        """Obtains OAuth2 bearer token from Flipkart Seller Auth endpoint."""
        if not self.is_configured() and client is None:
            return None

        endpoint = "https://api.flipkart.net/oauth-service/oauth/token"
        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=10.0)
            should_close = True

        try:
            res = await client.get(
                endpoint,
                params={
                    "grant_type": "client_credentials",
                    "scope": "Seller_api",
                },
                auth=(self.app_id or "dummy_app", self.app_secret or "dummy_secret"),
            )
            if res.status_code == 200:
                return res.json().get("access_token")
            logger.warning(f"Flipkart auth failed ({res.status_code}): {res.text}")
            return None
        except Exception as e:
            logger.warning(f"Flipkart auth exception: {str(e)}")
            return None
        finally:
            if should_close:
                await client.aclose()

    async def create_or_update_listing(
        self,
        sku: str,
        listing_payload: Dict[str, Any],
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Submits product listing to Flipkart Seller Hub."""
        is_valid, validation_errors = self.validate_listing_payload(listing_payload)
        if not is_valid:
            raise FlipkartAPIError(f"Flipkart listing validation rejected: {'; '.join(validation_errors)}")

        if not self.is_configured() and client is None:
            raise FlipkartAPIError("Flipkart Seller Hub credentials not configured. Application ID and App Secret are required.")

        access_token = await self.get_access_token(client=client)
        if not access_token and client is None:
            raise FlipkartAPIError("Failed to authenticate with Flipkart Seller API.")

        endpoint = f"{self.base_url}/v3/listings/{sku}"
        headers = {
            "Authorization": f"Bearer {access_token or 'test_token'}",
            "Content-Type": "application/json",
        }

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            res = await client.put(endpoint, json=listing_payload, headers=headers)
            if res.status_code in [200, 201]:
                data = res.json()
                return {
                    "sku": sku,
                    "listing_id": data.get("listing_id") or f"FLIP_{sku}",
                    "status": data.get("status", "ACTIVE"),
                    "raw_response": data,
                }
            else:
                raise FlipkartAPIError(f"Flipkart listing failed ({res.status_code}): {res.text}")
        finally:
            if should_close:
                await client.aclose()

    async def get_orders(
        self,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves orders from Flipkart Seller API."""
        if not self.is_configured() and client is None:
            return []

        access_token = await self.get_access_token(client=client)
        if not access_token and client is None:
            return []

        endpoint = f"{self.base_url}/v2/orders/search"
        headers = {"Authorization": f"Bearer {access_token or 'test_token'}"}
        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            res = await client.post(endpoint, json={"filter": {"states": ["APPROVED", "PACKED"]}}, headers=headers)
            if res.status_code == 200:
                return res.json().get("orderItems", [])
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch Flipkart orders: {str(e)}")
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
        """Updates stock quantity on Flipkart Seller Hub."""
        if not self.is_configured() and client is None:
            return False

        access_token = await self.get_access_token(client=client)
        if not access_token and client is None:
            return False

        endpoint = f"{self.base_url}/v3/listings/{sku}/inventory"
        headers = {
            "Authorization": f"Bearer {access_token or 'test_token'}",
            "Content-Type": "application/json",
        }
        body = {"product_id": sku, "locations": [{"id": "LOC_DEFAULT", "inventory": quantity}]}

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            res = await client.put(endpoint, json=body, headers=headers)
            return res.status_code in [200, 204]
        except Exception as e:
            logger.warning(f"Failed to update Flipkart inventory: {str(e)}")
            return False
        finally:
            if should_close:
                await client.aclose()

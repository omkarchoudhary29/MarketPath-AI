"""WooCommerce Storefront Connector.

Integrates with WooCommerce REST API v3 over HTTPS using Consumer Key and Secret.
Supports product creation, variant management, inventory sync, and order retrieval.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class WooCommerceError(Exception):
    """Custom exception for WooCommerce API errors."""
    pass


class WooCommerceService:
    """Service to interact with WooCommerce REST API."""

    def __init__(
        self,
        store_url: Optional[str] = None,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
    ):
        self.store_url = (store_url or getattr(settings, "WOOCOMMERCE_STORE_URL", "") or "").rstrip("/")
        self.consumer_key = consumer_key or getattr(settings, "WOOCOMMERCE_CONSUMER_KEY", "") or ""
        self.consumer_secret = consumer_secret or getattr(settings, "WOOCOMMERCE_CONSUMER_SECRET", "") or ""

    def is_configured(self) -> bool:
        """Checks if WooCommerce store credentials are configured."""
        return bool(
            self.store_url
            and self.consumer_key
            and self.consumer_secret
            and not self.consumer_key.startswith("your_")
            and len(self.consumer_key) > 5
        )

    def _get_auth(self) -> Tuple[str, str]:
        return (self.consumer_key, self.consumer_secret)

    async def verify_connection(self) -> Dict[str, Any]:
        """Tests store connectivity and returns store information."""
        if not self.is_configured():
            return {
                "connected": False,
                "status": "Setup Required",
                "message": "WooCommerce Store URL, Consumer Key, or Secret not configured.",
            }

        endpoint = f"{self.store_url}/wp-json/wc/v3/system_status"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(endpoint, auth=self._get_auth())
                if res.status_code == 200:
                    data = res.json()
                    env = data.get("environment", {})
                    return {
                        "connected": True,
                        "status": "Connected",
                        "store_name": env.get("site_title", "WooCommerce Store"),
                        "wc_version": env.get("version", "v3"),
                        "wp_version": env.get("wp_version", ""),
                    }
                else:
                    return {
                        "connected": False,
                        "status": "Connection Error",
                        "message": f"WooCommerce returned HTTP {res.status_code}: {res.text[:150]}",
                    }
        except Exception as e:
            logger.warning(f"WooCommerce verify connection failed: {str(e)}")
            return {
                "connected": False,
                "status": "Connection Error",
                "message": f"Network error connecting to {self.store_url}: {str(e)}",
            }

    async def create_product(
        self,
        payload: Dict[str, Any],
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Creates a new product listing on WooCommerce via POST /wp-json/wc/v3/products."""
        if not self.is_configured() and client is None:
            raise WooCommerceError("WooCommerce store credentials are not configured. Store URL, Consumer Key, and Secret are required.")

        endpoint = f"{self.store_url}/wp-json/wc/v3/products"
        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            res = await client.post(endpoint, json=payload, auth=self._get_auth())
            if res.status_code in [200, 201]:
                return res.json()
            else:
                raise WooCommerceError(f"WooCommerce product create failed ({res.status_code}): {res.text}")
        finally:
            if should_close:
                await client.aclose()

    @staticmethod
    def verify_webhook_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
        """Validates WooCommerce HMAC-SHA256 webhook signature."""
        import base64
        import hashlib
        import hmac
        if not signature_header or not secret:
            return False
        expected = base64.b64encode(
            hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
        ).decode("utf-8")
        return hmac.compare_digest(expected, signature_header)

    async def update_inventory(
        self,
        wc_product_id: int,
        stock_quantity: int,
        client: Optional[httpx.AsyncClient] = None,
    ) -> bool:
        """Updates product stock quantity on WooCommerce."""
        if not self.is_configured() and client is None:
            return False

        endpoint = f"{self.store_url}/wp-json/wc/v3/products/{wc_product_id}"
        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=10.0)
            should_close = True

        try:
            res = await client.put(
                endpoint,
                json={"manage_stock": True, "stock_quantity": stock_quantity},
                auth=self._get_auth(),
            )
            return res.status_code == 200
        finally:
            if should_close:
                await client.aclose()

    async def get_orders(
        self,
        status: str = "any",
        limit: int = 20,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves recent orders from WooCommerce."""
        if not self.is_configured() and client is None:
            return []

        endpoint = f"{self.store_url}/wp-json/wc/v3/orders"
        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            res = await client.get(
                endpoint,
                params={"status": status, "per_page": limit},
                auth=self._get_auth(),
            )
            if res.status_code == 200:
                return res.json()
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch WooCommerce orders: {str(e)}")
            return []
        finally:
            if should_close:
                await client.aclose()

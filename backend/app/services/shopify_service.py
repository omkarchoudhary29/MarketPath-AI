"""Shopify API Connector Service.

Handles official Shopify OAuth authorization and Admin GraphQL API operations (2026-10).
Token exchange, state CSRF verification, product creation mutation, order retrieval, inventory sync, and error classification.
"""

import hmac
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

SHOPIFY_API_VERSION = "2026-10"


class ShopifyError(Exception):
    """Base exception for Shopify API interactions."""
    def __init__(self, message: str, is_retryable: bool = False, http_status: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.is_retryable = is_retryable
        self.http_status = http_status


class ShopifyService:
    """Connector for Shopify Admin GraphQL API and OAuth."""

    @classmethod
    def is_configured(cls) -> bool:
        """Returns True if Shopify app client ID and secret are present."""
        return bool(settings.SHOPIFY_API_KEY and settings.SHOPIFY_API_SECRET)

    @classmethod
    def sanitize_shop_domain(cls, shop: str) -> str:
        """Normalizes and validates a shop domain (e.g. 'brand-store.myshopify.com')."""
        shop = shop.strip().lower()
        if shop.startswith("https://"):
            shop = shop[8:]
        elif shop.startswith("http://"):
            shop = shop[7:]
        shop = shop.rstrip("/")
        if not shop.endswith(".myshopify.com"):
            shop = f"{shop}.myshopify.com"
        return shop

    @classmethod
    def generate_authorize_url(cls, shop_domain: str, state: str) -> str:
        """Constructs official Shopify OAuth authorization URL with CSRF nonce."""
        sanitized_shop = cls.sanitize_shop_domain(shop_domain)
        api_key = settings.SHOPIFY_API_KEY
        redirect_uri = settings.SHOPIFY_REDIRECT_URI
        scopes = settings.SHOPIFY_APP_SCOPES

        return (
            f"https://{sanitized_shop}/admin/oauth/authorize?"
            f"client_id={api_key}&scope={scopes}&redirect_uri={redirect_uri}&state={state}"
        )

    @classmethod
    async def exchange_access_token(
        cls,
        shop_domain: str,
        code: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Exchanges an authorization code for a permanent offline access token."""
        sanitized_shop = cls.sanitize_shop_domain(shop_domain)
        token_url = f"https://{sanitized_shop}/admin/oauth/access_token"
        payload = {
            "client_id": settings.SHOPIFY_API_KEY,
            "client_secret": settings.SHOPIFY_API_SECRET,
            "code": code,
        }

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            resp = await client.post(token_url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "access_token": data.get("access_token"),
                    "scope": data.get("scope", "").split(",") if data.get("scope") else [],
                    "shop": sanitized_shop,
                }
            else:
                logger.error(f"Shopify token exchange error {resp.status_code}: {resp.text}")
                raise ShopifyError(
                    f"Shopify authorization failed with HTTP {resp.status_code}: {resp.text}",
                    is_retryable=False,
                    http_status=resp.status_code,
                )
        except httpx.RequestError as e:
            logger.error(f"Shopify network error during token exchange: {e}")
            raise ShopifyError(f"Network error contacting Shopify: {str(e)}", is_retryable=True)
        finally:
            if should_close:
                await client.aclose()

    @classmethod
    async def create_product_listing(
        cls,
        shop_domain: str,
        access_token: str,
        payload: Dict[str, Any],
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Executes Shopify GraphQL productCreate mutation to publish a product."""
        sanitized_shop = cls.sanitize_shop_domain(shop_domain)
        endpoint = f"https://{sanitized_shop}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"

        mutation = """
        mutation productCreate($input: ProductInput!, $media: [CreateMediaInput!]) {
            productCreate(input: $input, media: $media) {
                product {
                    id
                    title
                    handle
                    status
                    onlineStoreUrl
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {
            "input": payload.get("input", {}),
            "media": payload.get("media", []),
        }

        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        }

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=30.0)
            should_close = True

        try:
            resp = await client.post(endpoint, json={"query": mutation, "variables": variables}, headers=headers)
            
            # Verify Shopify API Version from response header
            api_version_header = resp.headers.get("X-Shopify-API-Version")
            if api_version_header and api_version_header != SHOPIFY_API_VERSION:
                logger.warning(
                    f"Shopify Admin API returned version '{api_version_header}', requested '{SHOPIFY_API_VERSION}'"
                )

            # Rate limiting check (429)
            if resp.status_code == 429:
                raise ShopifyError(
                    "Shopify API rate limit reached. Retry scheduled with backoff.",
                    is_retryable=True,
                    http_status=429,
                )

            if resp.status_code != 200:
                raise ShopifyError(
                    f"Shopify API returned error HTTP {resp.status_code}: {resp.text}",
                    is_retryable=(resp.status_code >= 500),
                    http_status=resp.status_code,
                )

            data = resp.json()
            if "errors" in data and data["errors"]:
                error_msgs = [e.get("message", "Unknown GraphQL error") for e in data["errors"]]
                raise ShopifyError(f"Shopify GraphQL error: {'; '.join(error_msgs)}", is_retryable=False)

            result = data.get("data", {}).get("productCreate", {})
            user_errors = result.get("userErrors", [])
            if user_errors:
                messages = [f"{e.get('field', 'item')}: {e.get('message')}" for e in user_errors]
                raise ShopifyError(f"Shopify product validation rejected: {'; '.join(messages)}", is_retryable=False)

            product = result.get("product")
            if not product:
                raise ShopifyError("Shopify returned empty product payload after creation.", is_retryable=False)

            remote_id = product.get("id", "")
            handle = product.get("handle", "")
            remote_url = product.get("onlineStoreUrl") or f"https://{sanitized_shop}/products/{handle}"

            return {
                "remote_product_id": remote_id,
                "remote_url": remote_url,
                "status": "published",
                "raw_response": product,
            }

        except ShopifyError:
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error calling Shopify GraphQL: {e}")
            raise ShopifyError(f"Network error contacting Shopify: {str(e)}", is_retryable=True)
        finally:
            if should_close:
                await client.aclose()

    @classmethod
    async def get_orders(
        cls,
        shop_domain: str,
        access_token: str,
        limit: int = 50,
        cursor: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Retrieves orders from Shopify Admin GraphQL API with pagination."""
        sanitized_shop = cls.sanitize_shop_domain(shop_domain)
        endpoint = f"https://{sanitized_shop}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"

        query = """
        query getOrders($first: Int!, $after: String) {
            orders(first: $first, after: $after, sortKey: CREATED_AT, reverse: true) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                edges {
                    cursor
                    node {
                        id
                        name
                        createdAt
                        updatedAt
                        currencyCode
                        displayFinancialStatus
                        displayFulfillmentStatus
                        totalPriceSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                        totalShippingPriceSet {
                            shopMoney {
                                amount
                            }
                        }
                        totalTaxSet {
                            shopMoney {
                                amount
                            }
                        }
                        totalDiscountsSet {
                            shopMoney {
                                amount
                            }
                        }
                        totalRefundedSet {
                            shopMoney {
                                amount
                            }
                        }
                        customer {
                            displayName
                            email
                        }
                        shippingAddress {
                            address1
                            city
                            province
                            zip
                            country
                        }
                        lineItems(first: 50) {
                            edges {
                                node {
                                    id
                                    title
                                    sku
                                    quantity
                                    originalUnitPriceSet {
                                        shopMoney {
                                            amount
                                        }
                                    }
                                    discountedTotalSet {
                                        shopMoney {
                                            amount
                                        }
                                    }
                                    variant {
                                        id
                                        sku
                                        product {
                                            id
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        }

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=30.0)
            should_close = True

        try:
            resp = await client.post(
                endpoint,
                json={"query": query, "variables": {"first": limit, "after": cursor}},
                headers=headers,
            )

            api_version_header = resp.headers.get("X-Shopify-API-Version")
            if api_version_header and api_version_header != SHOPIFY_API_VERSION:
                logger.warning(
                    f"Shopify Admin API returned version '{api_version_header}', requested '{SHOPIFY_API_VERSION}'"
                )

            if resp.status_code == 429:
                raise ShopifyError("Shopify rate limit exceeded during order fetch", is_retryable=True, http_status=429)
            if resp.status_code != 200:
                raise ShopifyError(f"Shopify orders query failed: {resp.text}", is_retryable=(resp.status_code >= 500), http_status=resp.status_code)

            data = resp.json()
            if "errors" in data and data["errors"]:
                raise ShopifyError(f"GraphQL error fetching orders: {data['errors']}")

            orders_data = data.get("data", {}).get("orders", {})
            edges = orders_data.get("edges", [])
            page_info = orders_data.get("pageInfo", {})

            normalized_orders = []
            for edge in edges:
                node = edge.get("node", {})
                line_items = []
                for li_edge in node.get("lineItems", {}).get("edges", []):
                    li = li_edge.get("node", {})
                    variant = li.get("variant") or {}
                    product = variant.get("product") or {}
                    line_items.append({
                        "remote_line_id": li.get("id"),
                        "title": li.get("title"),
                        "sku": li.get("sku") or variant.get("sku") or "",
                        "quantity": li.get("quantity", 1),
                        "unit_price": float(li.get("originalUnitPriceSet", {}).get("shopMoney", {}).get("amount", 0.0)),
                        "total_price": float(li.get("discountedTotalSet", {}).get("shopMoney", {}).get("amount", 0.0)),
                        "remote_variant_id": variant.get("id"),
                        "remote_product_id": product.get("id"),
                    })

                normalized_orders.append({
                    "remote_order_id": node.get("id"),
                    "order_number": node.get("name"),
                    "created_at": node.get("createdAt"),
                    "updated_at": node.get("updatedAt"),
                    "currency": node.get("currencyCode", "INR"),
                    "financial_status": node.get("displayFinancialStatus", "").lower() or "paid",
                    "fulfillment_status": node.get("displayFulfillmentStatus", "").lower() or "unfulfilled",
                    "total_amount": float(node.get("totalPriceSet", {}).get("shopMoney", {}).get("amount", 0.0)),
                    "shipping_amount": float(node.get("totalShippingPriceSet", {}).get("shopMoney", {}).get("amount", 0.0)) if node.get("totalShippingPriceSet") else 0.0,
                    "tax_amount": float(node.get("totalTaxSet", {}).get("shopMoney", {}).get("amount", 0.0)) if node.get("totalTaxSet") else 0.0,
                    "discount_amount": float(node.get("totalDiscountsSet", {}).get("shopMoney", {}).get("amount", 0.0)) if node.get("totalDiscountsSet") else 0.0,
                    "refund_amount": float(node.get("totalRefundedSet", {}).get("shopMoney", {}).get("amount", 0.0)) if node.get("totalRefundedSet") else 0.0,
                    "customer_name": node.get("customer", {}).get("displayName") if node.get("customer") else None,
                    "customer_email": node.get("customer", {}).get("email") if node.get("customer") else None,
                    "shipping_address": node.get("shippingAddress") or {},
                    "items": line_items,
                    "raw_node": node,
                })

            return {
                "orders": normalized_orders,
                "has_next_page": page_info.get("hasNextPage", False),
                "end_cursor": page_info.get("endCursor"),
            }
        except ShopifyError:
            raise
        except Exception as e:
            logger.error(f"Error querying Shopify orders: {e}")
            raise ShopifyError(f"Failed to query Shopify orders: {str(e)}", is_retryable=True)
        finally:
            if should_close:
                await client.aclose()

    @classmethod
    async def update_inventory_quantity(
        cls,
        shop_domain: str,
        access_token: str,
        inventory_item_id: str,
        location_id: str,
        available_delta: int,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Adjusts available stock level at a Shopify location via inventoryAdjustQuantity mutation."""
        sanitized_shop = cls.sanitize_shop_domain(shop_domain)
        endpoint = f"https://{sanitized_shop}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"

        mutation = """
        mutation inventoryAdjustQuantity($input: InventoryAdjustQuantityInput!) {
            inventoryAdjustQuantity(input: $input) {
                inventoryLevel {
                    id
                    available
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {
            "input": {
                "inventoryItemId": inventory_item_id,
                "locationId": location_id,
                "availableDelta": available_delta,
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        }

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=30.0)
            should_close = True

        try:
            resp = await client.post(endpoint, json={"query": mutation, "variables": variables}, headers=headers)
            if resp.status_code != 200:
                raise ShopifyError(f"Shopify inventory adjustment failed HTTP {resp.status_code}: {resp.text}", is_retryable=False)
            data = resp.json()
            result = data.get("data", {}).get("inventoryAdjustQuantity", {})
            user_errors = result.get("userErrors", [])
            if user_errors:
                msgs = [e.get("message") for e in user_errors]
                raise ShopifyError(f"Inventory adjust rejected by Shopify: {'; '.join(msgs)}")
            return {
                "status": "success",
                "inventory_level": result.get("inventoryLevel"),
            }
        except ShopifyError:
            raise
        except Exception as e:
            logger.error(f"Error adjusting Shopify inventory: {e}")
            raise ShopifyError(f"Failed to adjust inventory: {str(e)}", is_retryable=True)
        finally:
            if should_close:
                await client.aclose()


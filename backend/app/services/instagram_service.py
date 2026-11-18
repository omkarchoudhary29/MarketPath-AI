"""Instagram Graph API Connector Service.

Handles official Meta OAuth authorization and Instagram Graph API organic publishing.
Supports eligible professional accounts (Business & Creator) linked to Facebook Pages.
Two-step container publishing flow: /media -> /media_publish.
"""

import json
import logging
from typing import Any, Dict, Optional, Tuple
import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def get_graph_api_version() -> str:
    ver = getattr(settings, "META_GRAPH_API_VERSION", "v26.0")
    # Disallow expired versions
    try:
        ver_num = float(ver.lstrip("v"))
        if ver_num < 21.0:
            raise ValueError(f"Meta Graph API version {ver} is deprecated/expired. Version must be >= v21.0.")
    except Exception as e:
        if "deprecated" in str(e):
            raise
    return ver

GRAPH_API_VERSION = get_graph_api_version()


class InstagramError(Exception):
    """Base exception for Instagram Graph API interactions."""
    def __init__(self, message: str, is_retryable: bool = False, http_status: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.is_retryable = is_retryable
        self.http_status = http_status


class InstagramService:
    """Connector for Instagram Graph API and Meta OAuth."""

    @classmethod
    def is_configured(cls) -> bool:
        """Returns True if Meta app ID and secret are present in configuration."""
        return bool(settings.META_APP_ID and settings.META_APP_SECRET)

    @classmethod
    def generate_authorize_url(cls, state: str) -> str:
        """Constructs official Meta OAuth dialog URL with CSRF state nonce."""
        app_id = settings.META_APP_ID
        redirect_uri = settings.META_REDIRECT_URI
        scopes = settings.META_APP_SCOPES

        return (
            f"https://www.facebook.com/{GRAPH_API_VERSION}/dialog/oauth?"
            f"client_id={app_id}&redirect_uri={redirect_uri}&state={state}&scope={scopes}&response_type=code"
        )

    @classmethod
    async def exchange_access_token(
        cls,
        code: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Exchanges an authorization code for a long-lived Instagram professional account token."""
        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            # 1. Exchange code for short-lived user token
            token_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token"
            params = {
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "redirect_uri": settings.META_REDIRECT_URI,
                "code": code,
            }
            resp = await client.get(token_url, params=params)
            if resp.status_code != 200:
                raise InstagramError(
                    f"Meta OAuth token exchange failed (HTTP {resp.status_code}): {resp.text}",
                    is_retryable=False,
                    http_status=resp.status_code,
                )
            token_data = resp.json()
            short_token = token_data.get("access_token")

            # 2. Exchange short-lived token for long-lived user token (60-day expiry)
            exchange_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token"
            exchange_params = {
                "grant_type": "fb_exchange_token",
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "fb_exchange_token": short_token,
            }
            long_resp = await client.get(exchange_url, params=exchange_params)
            long_token = short_token
            if long_resp.status_code == 200:
                long_token = long_resp.json().get("access_token", short_token)

            # 3. Find connected Instagram Professional Account
            accounts_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/me/accounts"
            accounts_resp = await client.get(
                accounts_url,
                params={
                    "access_token": long_token,
                    "fields": "id,name,instagram_business_account{id,username,name}",
                },
            )
            if accounts_resp.status_code != 200:
                raise InstagramError(
                    f"Failed to fetch connected Facebook Pages: {accounts_resp.text}",
                    is_retryable=False,
                )

            accounts_data = accounts_resp.json()
            pages = accounts_data.get("data", [])
            ig_account = None
            page_name = "Default Page"

            for page in pages:
                if "instagram_business_account" in page and page["instagram_business_account"]:
                    ig_account = page["instagram_business_account"]
                    page_name = page.get("name", "Page")
                    break

            if not ig_account:
                raise InstagramError(
                    "No eligible Instagram Professional (Business/Creator) account was found linked to your Facebook Pages. "
                    "Please ensure your Instagram account is switched to Professional and connected to a Facebook Page.",
                    is_retryable=False,
                )

            return {
                "access_token": long_token,
                "account_identifier": ig_account.get("id"),
                "account_name": f"@{ig_account.get('username', 'instagram_user')} ({page_name})",
                "scopes": settings.META_APP_SCOPES.split(","),
            }

        except InstagramError:
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error during Instagram OAuth: {e}")
            raise InstagramError(f"Network error contacting Meta Graph API: {str(e)}", is_retryable=True)
        finally:
            if should_close:
                await client.aclose()

    @classmethod
    async def publish_organic_post(
        cls,
        ig_user_id: str,
        access_token: str,
        payload: Dict[str, Any],
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Publishes an organic feed photo via two-step container flow."""
        image_url = payload.get("image_url")
        caption = payload.get("caption", "")

        if not image_url:
            raise InstagramError("Instagram publishing requires a valid image_url.", is_retryable=False)

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=30.0)
            should_close = True

        try:
            # Step A: Create media container
            container_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{ig_user_id}/media"
            container_params = {
                "image_url": image_url,
                "caption": caption,
                "access_token": access_token,
            }
            container_resp = await client.post(container_url, data=container_params)
            if container_resp.status_code != 200:
                err_data = container_resp.json() if container_resp.headers.get("content-type", "").startswith("application/json") else {}
                err_msg = err_data.get("error", {}).get("message", container_resp.text)
                raise InstagramError(
                    f"Instagram media container creation failed (HTTP {container_resp.status_code}): {err_msg}",
                    is_retryable=(container_resp.status_code >= 500),
                    http_status=container_resp.status_code,
                )

            creation_id = container_resp.json().get("id")
            if not creation_id:
                raise InstagramError("Instagram API returned empty container ID.", is_retryable=False)

            # Step B: Publish media container
            publish_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{ig_user_id}/media_publish"
            publish_params = {
                "creation_id": creation_id,
                "access_token": access_token,
            }
            publish_resp = await client.post(publish_url, data=publish_params)
            if publish_resp.status_code != 200:
                err_data = publish_resp.json() if publish_resp.headers.get("content-type", "").startswith("application/json") else {}
                err_msg = err_data.get("error", {}).get("message", publish_resp.text)
                raise InstagramError(
                    f"Instagram media publishing failed (HTTP {publish_resp.status_code}): {err_msg}",
                    is_retryable=(publish_resp.status_code >= 500),
                    http_status=publish_resp.status_code,
                )

            media_id = publish_resp.json().get("id")

            # Step C: Fetch permalink
            permalink = f"https://www.instagram.com/p/{media_id}/"
            try:
                permalink_resp = await client.get(
                    f"https://graph.facebook.com/{GRAPH_API_VERSION}/{media_id}",
                    params={"fields": "permalink", "access_token": access_token},
                )
                if permalink_resp.status_code == 200:
                    permalink = permalink_resp.json().get("permalink", permalink)
            except Exception as e:
                logger.warning(f"Failed to fetch Instagram permalink: {e}")

            return {
                "remote_product_id": media_id,
                "remote_url": permalink,
                "status": "published",
                "raw_response": publish_resp.json(),
            }

        except InstagramError:
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error calling Instagram Graph API: {e}")
            raise InstagramError(f"Network error contacting Instagram: {str(e)}", is_retryable=True)
        finally:
            if should_close:
                await client.aclose()


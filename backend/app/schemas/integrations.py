import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChannelConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel_type: str
    account_identifier: str
    account_name: str
    granted_scopes: List[str]
    status: str  # active, expired, revoked, error
    last_synced_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class IntegrationStatusItem(BaseModel):
    platform: str
    display_name: str
    description: str
    channel_group: str = "storefronts"  # storefronts, marketplaces, social, quick_commerce
    connection_status: str  # Not Connected, Setup Required, Awaiting Authorization, Connected, Expired, Permission Required, Developer Approval Pending, Connection Error, Partner Access Required, Coming Soon
    partner_status: Optional[str] = None
    is_configured: bool
    connection_id: Optional[uuid.UUID] = None
    account_identifier: Optional[str] = None
    account_name: Optional[str] = None
    last_synced_at: Optional[datetime.datetime] = None
    granted_scopes: List[str] = Field(default_factory=list)
    required_env_vars: List[str] = Field(default_factory=list)
    setup_instructions: Optional[str] = None


class ShopifyAuthorizeRequest(BaseModel):
    shop_domain: str = Field(..., min_length=4, max_length=150, description="e.g. brand-store.myshopify.com")


class OAuthAuthorizeResponse(BaseModel):
    authorization_url: str
    state: str
    platform: str


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str
    shop: Optional[str] = None


class WooCommerceConnectRequest(BaseModel):
    store_url: str = Field(..., description="WooCommerce store URL, e.g. https://mystore.com")
    consumer_key: str = Field(..., description="REST API Consumer Key (ck_...)")
    consumer_secret: str = Field(..., description="REST API Consumer Secret (cs_...)")


class AmazonConnectRequest(BaseModel):
    client_id: str = Field(..., description="AWS LWA App Client ID")
    client_secret: str = Field(..., description="AWS LWA App Client Secret")
    refresh_token: str = Field(..., description="LWA Authorization Refresh Token")
    seller_id: str = Field(..., description="Amazon India Merchant / Seller ID")


class FlipkartConnectRequest(BaseModel):
    app_id: str = Field(..., description="Flipkart Developer App ID")
    app_secret: str = Field(..., description="Flipkart Developer App Secret")



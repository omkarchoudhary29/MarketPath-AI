"""Channel Capability Registry.

Central authoritative specification of supported selling channels, storefronts,
marketplaces, quick commerce partners, and social commerce platforms.

Documents actual developer onboarding requirements, required API scopes, rate limits,
supported operations (create, update, variants, stock, price, orders), regional availability,
and honest operational readiness statuses.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ChannelCapability(BaseModel):
    product_creation: bool
    listing_updates: bool
    variants_supported: bool
    product_media_sync: bool
    price_updates: bool
    inventory_updates: bool
    order_retrieval: bool
    order_status_sync: bool
    sales_reporting: bool
    returns_refunds: bool
    listing_status_polling: bool
    webhooks_supported: bool


class ChannelSpecification(BaseModel):
    platform: str
    display_name: str
    channel_group: str  # storefront, marketplace, quick_commerce, social, product_feed, retail_partner
    status: str  # Connected, Available, Setup Required, Approval Required, Partner Access Required, Coming Soon
    description: str
    regional_availability: str
    developer_onboarding: str
    required_api_scopes: List[str]
    rate_limits: str
    capabilities: ChannelCapability
    setup_instructions: str
    required_env_vars: List[str]
    notes: Optional[str] = None


CHANNEL_REGISTRY: Dict[str, ChannelSpecification] = {
    "shopify": ChannelSpecification(
        platform="shopify",
        display_name="Shopify",
        channel_group="storefront",
        status="Available",
        description="Global D2C e-commerce storefront platform via Admin GraphQL & REST APIs.",
        regional_availability="India & Global (Multi-currency, INR native)",
        developer_onboarding="Create a Custom App or Public Partner App in Shopify Partners Console. Generate Client ID & Secret.",
        required_api_scopes=[
            "write_products", "read_products",
            "write_inventory", "read_inventory",
            "read_orders", "write_orders",
            "read_customers"
        ],
        rate_limits="Standard Leaky Bucket: 40 requests/sec (REST) / 50-100 cost points/sec (GraphQL Admin API)",
        capabilities=ChannelCapability(
            product_creation=True,
            listing_updates=True,
            variants_supported=True,
            product_media_sync=True,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=True,
            order_status_sync=True,
            sales_reporting=True,
            returns_refunds=True,
            listing_status_polling=True,
            webhooks_supported=True,
        ),
        setup_instructions="Navigate to Shopify Store Admin > Settings > Apps and sales channels > Develop apps. Create custom app, assign Product and Order scopes, and install.",
        required_env_vars=["SHOPIFY_API_KEY", "SHOPIFY_API_SECRET", "SHOPIFY_REDIRECT_URI"],
        notes="Production-ready OAuth2 authorization and bi-directional product/inventory sync supported."
    ),
    "woocommerce": ChannelSpecification(
        platform="woocommerce",
        display_name="WooCommerce",
        channel_group="storefront",
        status="Available",
        description="WordPress-based open-source storefront powered by WooCommerce REST API v3.",
        regional_availability="India & Global (All currencies and hosting providers)",
        developer_onboarding="Generate REST API Consumer Key and Consumer Secret with Read/Write permissions from WordPress Admin.",
        required_api_scopes=["read_write_products", "read_write_orders", "read_write_inventory"],
        rate_limits="Server-dependent (typical WordPress hosting allows 60-120 req/min)",
        capabilities=ChannelCapability(
            product_creation=True,
            listing_updates=True,
            variants_supported=True,
            product_media_sync=True,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=True,
            order_status_sync=True,
            sales_reporting=True,
            returns_refunds=True,
            listing_status_polling=True,
            webhooks_supported=True,
        ),
        setup_instructions="Go to WP Admin > WooCommerce > Settings > Advanced > REST API > Add Key. Select Read/Write permissions and copy Consumer Key and Secret.",
        required_env_vars=["WOOCOMMERCE_STORE_URL", "WOOCOMMERCE_CONSUMER_KEY", "WOOCOMMERCE_CONSUMER_SECRET"],
        notes="Direct REST API connector with basic auth over HTTPS."
    ),
    "amazon": ChannelSpecification(
        platform="amazon",
        display_name="Amazon India",
        channel_group="marketplace",
        status="Setup Required",
        description="India's leading consumer marketplace via Amazon Selling Partner API (SP-API).",
        regional_availability="India (amazon.in - MarketplaceId: A21TJRUUN4KGV)",
        developer_onboarding="Requires Amazon Professional Selling Account, AWS IAM Role, and SP-API Developer Application approval with Restricted Data Token (RDT).",
        required_api_scopes=[
            "sellingpartnerapi::pricing",
            "sellingpartnerapi::listings_items",
            "sellingpartnerapi::orders",
            "sellingpartnerapi::inventory"
        ],
        rate_limits="SP-API Listings: 5 req/sec (Burst 10). Orders: 0.5 req/sec (Burst 30). Strict token bucket.",
        capabilities=ChannelCapability(
            product_creation=True,
            listing_updates=True,
            variants_supported=True,
            product_media_sync=True,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=True,
            order_status_sync=True,
            sales_reporting=True,
            returns_refunds=True,
            listing_status_polling=True,
            webhooks_supported=True,
        ),
        setup_instructions="Register developer profile in Amazon Seller Central. Create AWS LWA App and configure SP-API Role ARN. Enter Refresh Token and LWA Client Secret.",
        required_env_vars=["AMAZON_SP_API_CLIENT_ID", "AMAZON_SP_API_CLIENT_SECRET", "AMAZON_REFRESH_TOKEN", "AMAZON_AWS_ACCESS_KEY_ID", "AMAZON_AWS_SECRET_ACCESS_KEY", "AMAZON_ROLE_ARN"],
        notes="Product type definition schemas (JSON Schema) enforce strict mandatory fields (item_dimensions, bullet_points, country_of_origin)."
    ),
    "flipkart": ChannelSpecification(
        platform="flipkart",
        display_name="Flipkart",
        channel_group="marketplace",
        status="Setup Required",
        description="Premier Indian consumer marketplace via Flipkart Seller Hub APIs.",
        regional_availability="India (Pan-India seller network)",
        developer_onboarding="Requires active Flipkart Seller account, registered GSTIN, and Flipkart Developer API App with Application ID & Secret.",
        required_api_scopes=["listings_read_write", "orders_read_write", "shipments_read_write"],
        rate_limits="Listing API: 10 req/sec; Order API: 5 req/sec",
        capabilities=ChannelCapability(
            product_creation=True,
            listing_updates=True,
            variants_supported=True,
            product_media_sync=True,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=True,
            order_status_sync=True,
            sales_reporting=True,
            returns_refunds=True,
            listing_status_polling=True,
            webhooks_supported=False,  # Flipkart uses polling models for order feeds
        ),
        setup_instructions="Apply for developer access in Flipkart Seller Hub API Portal. Generate App ID and App Secret. Whitelist static server IP address.",
        required_env_vars=["FLIPKART_APP_ID", "FLIPKART_APP_SECRET"],
        notes="Flipkart enforces category-specific Vertical Attributes, mandatory MRP, Selling Price, and packaging weight specs."
    ),
    "google_merchant": ChannelSpecification(
        platform="google_merchant",
        display_name="Google Merchant Center",
        channel_group="product_feed",
        status="Available",
        description="Synchronize master catalogue to Google Shopping, Free Product Listings, and Performance Max ads.",
        regional_availability="India & Global",
        developer_onboarding="Claim and verify domain in Google Merchant Center. Create Content API for Shopping service account or automated XML/RSS feed.",
        required_api_scopes=["https://www.googleapis.com/auth/content"],
        rate_limits="Content API: 10,000 requests/day per sub-account",
        capabilities=ChannelCapability(
            product_creation=True,
            listing_updates=True,
            variants_supported=True,
            product_media_sync=True,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=False,  # Google Shopping feed pushes items, orders occur on brand storefront
            order_status_sync=False,
            sales_reporting=True,
            returns_refunds=False,
            listing_status_polling=True,
            webhooks_supported=False,
        ),
        setup_instructions="Connect Google Merchant Center Account ID and verify storefront URL. MarketPath generates auto-refreshing compliant RSS/XML product feed.",
        required_env_vars=["GOOGLE_MERCHANT_ID", "GOOGLE_SERVICE_ACCOUNT_JSON"],
        notes="Selected as core 5th integration target due to universal eligibility for Indian D2C brands (Etsy requires handmade vintage verification and has restricted onboarding in India; eBay India operates through cross-border export programs with limited domestic retail APIs)."
    ),
    "myntra": ChannelSpecification(
        platform="myntra",
        display_name="Myntra Partner Portal",
        channel_group="marketplace",
        status="Partner Access Required",
        description="Curated fashion & lifestyle marketplace under Flipkart Group.",
        regional_availability="India",
        developer_onboarding="Requires formal supplier agreement and Myntra Partner Hub credentials with Vendor Code.",
        required_api_scopes=["catalog_feed", "inventory_push"],
        rate_limits="Batch SFTP/API feeds",
        capabilities=ChannelCapability(
            product_creation=True,
            listing_updates=True,
            variants_supported=True,
            product_media_sync=True,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=True,
            order_status_sync=True,
            sales_reporting=True,
            returns_refunds=True,
            listing_status_polling=True,
            webhooks_supported=False,
        ),
        setup_instructions="Sign brand partner agreement with Myntra category team. Configure Vendor Code and Partner Token.",
        required_env_vars=["MYNTRA_PARTNER_TOKEN", "MYNTRA_VENDOR_CODE"],
        notes="Closed brand onboarding. MarketPath provides exportable Myntra-compliant catalog Excel sheets while API access is pending."
    ),
    "ajio": ChannelSpecification(
        platform="ajio",
        display_name="AJIO (Reliance Retail)",
        channel_group="retail_partner",
        status="Partner Access Required",
        description="Reliance Retail's curated fashion, lifestyle, and artisanal D2C destination.",
        regional_availability="India",
        developer_onboarding="Requires direct brand supplier contract with Reliance Retail / AJIO B2B portal.",
        required_api_scopes=["reliance_supplier_catalog"],
        rate_limits="Batch feed sync",
        capabilities=ChannelCapability(
            product_creation=False,  # AJIO enforces manual catalog onboarding
            listing_updates=True,
            variants_supported=True,
            product_media_sync=True,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=True,
            order_status_sync=True,
            sales_reporting=True,
            returns_refunds=True,
            listing_status_polling=True,
            webhooks_supported=False,
        ),
        setup_instructions="Direct API access requires an enterprise brand supplier contract with Reliance Retail / AJIO B2B portal.",
        required_env_vars=["AJIO_ENTERPRISE_MERCHANT_KEY"],
        notes="Closed marketplace. Integration requires manual brand onboarding paperwork."
    ),
    "blinkit": ChannelSpecification(
        platform="blinkit",
        display_name="Blinkit",
        channel_group="quick_commerce",
        status="Available",
        description="10-minute grocery and essential quick commerce delivery across 30+ tier-1 Indian cities.",
        regional_availability="Tier 1 & Tier 2 Indian Metros",
        developer_onboarding="Requires Blinkit Brands Partner portal credentials and dark store mapping.",
        required_api_scopes=["darkstore_inventory_sync", "orders_read"],
        rate_limits="30 requests/min",
        capabilities=ChannelCapability(
            product_creation=False,  # Ingestion managed through Blinkit Brands catalogue team
            listing_updates=True,
            variants_supported=True,
            product_media_sync=True,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=True,
            order_status_sync=True,
            sales_reporting=True,
            returns_refunds=False,
            listing_status_polling=True,
            webhooks_supported=True,
        ),
        setup_instructions="Provide Blinkit Brand ID and API Key from Brands Portal. Map dark store warehouses to local inventory.",
        required_env_vars=["BLINKIT_BRAND_ID", "BLINKIT_API_KEY"],
        notes="Quick commerce dark store inventory sync with low-latency stock buffers."
    ),
    "zepto": ChannelSpecification(
        platform="zepto",
        display_name="Zepto",
        channel_group="quick_commerce",
        status="Partner Access Required",
        description="Instant delivery quick commerce network with closed brand partner onboarding.",
        regional_availability="Major Indian Metros (Mumbai, Pune, Delhi NCR, Bengaluru, Hyderabad, Chennai)",
        developer_onboarding="Requires direct commercial partnership agreement with Zepto Brands & Procurement team.",
        required_api_scopes=["zepto_partner_inventory"],
        rate_limits="Managed partner stream",
        capabilities=ChannelCapability(
            product_creation=False,
            listing_updates=False,
            variants_supported=True,
            product_media_sync=False,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=True,
            order_status_sync=True,
            sales_reporting=True,
            returns_refunds=False,
            listing_status_polling=True,
            webhooks_supported=False,
        ),
        setup_instructions="Zepto operates closed brand partner APIs. Direct commercial partnership with Zepto Brands team is mandatory before API access is granted.",
        required_env_vars=["ZEPTO_PARTNER_KEY"],
        notes="Direct brand partnership required before API credentials can be issued."
    ),
    "instagram": ChannelSpecification(
        platform="instagram",
        display_name="Instagram Professional",
        channel_group="social",
        status="Available",
        description="Organic product feed posts and carousels to Instagram Business/Creator account via Meta Graph API.",
        regional_availability="Global",
        developer_onboarding="Meta for Developers App with instagram_content_publish scope, linked Facebook Page and Instagram Professional Account.",
        required_api_scopes=["instagram_basic", "instagram_content_publish", "pages_show_list"],
        rate_limits="200 API calls per hour per user",
        capabilities=ChannelCapability(
            product_creation=True,  # In the form of Shoppable Feed Posts
            listing_updates=False,
            variants_supported=False,
            product_media_sync=True,
            price_updates=False,
            inventory_updates=False,
            order_retrieval=False,
            order_status_sync=False,
            sales_reporting=True,
            returns_refunds=False,
            listing_status_polling=True,
            webhooks_supported=True,
        ),
        setup_instructions="Authorize via Meta OAuth. Select Facebook Page and linked Instagram Business account.",
        required_env_vars=["META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI"],
        notes="Publishing creates organic posts and carousels with product tags."
    ),
    "ebay": ChannelSpecification(
        platform="ebay",
        display_name="eBay Global Export",
        channel_group="marketplace",
        status="Approval Required",
        description="Cross-border international export marketplace via eBay REST Fulfillment and Inventory APIs.",
        regional_availability="Global Exports (US/UK/EU export programs from India)",
        developer_onboarding="Requires active eBay developer account, registered export business with IEC (Import Export Code), and Payoneer managed payments.",
        required_api_scopes=["https://api.ebay.com/oauth/api_scope/sell.inventory", "https://api.ebay.com/oauth/api_scope/sell.fulfillment"],
        rate_limits="Standard REST: 5,000 calls/day for Inventory API",
        capabilities=ChannelCapability(
            product_creation=True,
            listing_updates=True,
            variants_supported=True,
            product_media_sync=True,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=True,
            order_status_sync=True,
            sales_reporting=True,
            returns_refunds=True,
            listing_status_polling=True,
            webhooks_supported=True,
        ),
        setup_instructions="Apply for eBay Developer Program. Configure OAuth App with sell.inventory scopes and link verified Payoneer account.",
        required_env_vars=["EBAY_APP_ID", "EBAY_CERT_ID", "EBAY_DEV_ID", "EBAY_USER_TOKEN"],
        notes="Evaluated for 5th core slot. Requires IEC and Payoneer; domestic retail selling inside India is discontinued on eBay.in."
    ),
    "etsy": ChannelSpecification(
        platform="etsy",
        display_name="Etsy",
        channel_group="marketplace",
        status="Temporarily Unavailable",
        description="Global marketplace for handmade, vintage, and craft supplies via Etsy Open API v3.",
        regional_availability="Restricted in India (Etsy Payments onboarding paused for new Indian shops)",
        developer_onboarding="Requires verified Etsy Seller account and Open API v3 developer app key.",
        required_api_scopes=["listings_r", "listings_w", "transactions_r"],
        rate_limits="10 requests/sec (Burst 15)",
        capabilities=ChannelCapability(
            product_creation=True,
            listing_updates=True,
            variants_supported=True,
            product_media_sync=True,
            price_updates=True,
            inventory_updates=True,
            order_retrieval=True,
            order_status_sync=True,
            sales_reporting=True,
            returns_refunds=False,
            listing_status_polling=True,
            webhooks_supported=False,
        ),
        setup_instructions="Etsy Payments onboarding is currently paused for new Indian seller accounts. Existing shops with grandfathered access can connect API keys.",
        required_env_vars=["ETSY_API_KEY", "ETSY_SHARED_SECRET"],
        notes="Etsy enforces strict handmade/vintage proof. New Indian seller registrations are currently suspended pending Etsy Payments integration in India."
    ),
}


def get_channel_specification(platform: str) -> Optional[ChannelSpecification]:
    """Retrieves authoritative channel capability specification."""
    return CHANNEL_REGISTRY.get(platform.lower())


def list_all_channels() -> List[ChannelSpecification]:
    """Returns all registered sales channels and marketplaces."""
    return list(CHANNEL_REGISTRY.values())

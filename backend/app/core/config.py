import base64
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = Field(default="development", description="Application environment (development, staging, production)")
    PROJECT_NAME: str = "MarketPath AI"
    API_V1_PREFIX: str = "/api/v1"
    PORT: int = Field(default=8000, description="HTTP listening port provided by platform (e.g. Railway $PORT)")

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./marketpath.db",
        description="Async database connection string"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def transform_database_url(cls, v: str) -> str:
        """Transforms standard postgres:// and postgresql:// URIs into asyncpg-compatible dialect."""
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Supabase Auth
    SUPABASE_URL: str = Field(default="https://example.supabase.co", description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(default="mock-anon-key", description="Supabase anonymous public key")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="mock-service-role-key", description="Supabase service role secret (backend only)")
    SUPABASE_JWT_JWKS_URL: Optional[str] = Field(default=None, description="Supabase JWKS URL for JWT validation")
    SUPABASE_JWT_SECRET: Optional[str] = Field(default=None, description="Fallback Supabase JWT secret for HMAC validation")

    # Security & Encryption
    SECRET_KEY: str = Field(default="insecure-marketpath-secret-key-change-in-prod-32chars", description="Application secret key")
    ENCRYPTION_MASTER_KEY: str = Field(
        default="MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE=",  # Base64 encoded 32-byte key
        description="AES-256 master key for encrypting external tokens"
    )

    # CORS & URLs
    FRONTEND_URL: str = Field(default="http://localhost:5173", description="Frontend origin for CORS")
    BACKEND_URL: str = Field(default="http://localhost:8000", description="Backend URL")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # Cloudinary & AI (Environment placeholders for upcoming modules)
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash-lite", description="Configured Gemini model")

    # Shopify Partner App Configuration
    SHOPIFY_API_KEY: Optional[str] = None
    SHOPIFY_API_SECRET: Optional[str] = None
    SHOPIFY_APP_SCOPES: str = "write_products,read_products,write_inventory,read_inventory,read_orders"
    SHOPIFY_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/shopify/callback"

    # Meta Graph & Marketing API Independent Versioning (v26.0 current, >= v21.0 required)
    META_GRAPH_API_VERSION: str = Field(default="v26.0", description="Meta Graph API version for Instagram & Graph endpoints")
    META_MARKETING_API_VERSION: str = Field(default="v26.0", description="Meta Marketing API version for Ads Management")
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    META_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/instagram/callback"
    META_ADS_ACCESS_TOKEN: Optional[str] = None

    # Platform Admin Bootstrap
    PLATFORM_ADMIN_BOOTSTRAP_EMAIL: str = Field(default="operator@marketpath.ai", description="Primary Platform Admin account email")
    MARKETPATH_BOOTSTRAP_ADMIN: bool = Field(default=True, description="Enable one-time Platform Admin bootstrap execution")
    DEMO_ACCOUNTS_ENABLED: bool = Field(default=True, description="Enable demo account experiences")

    # Transactional Email Configuration (Honest delivery reporting)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "notifications@marketpath.ai"
    EMAIL_FROM_NAME: str = "MarketPath AI"
    BOOKING_NOTIFICATION_TO: str = "consultations@marketpath.ai"
    EMAIL_PROVIDER: str = "smtp"
    EMAIL_API_KEY: Optional[str] = None
    BREVO_API_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    META_APP_SCOPES: str = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Fail-fast validation for critical secrets and encryption keys in production."""
        if self.APP_ENV == "production":
            # 1. SECRET_KEY validation
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("In production, SECRET_KEY must be configured with at least 32 characters.")
            insecure_patterns = ["insecure", "change-in-prod", "placeholder", "dev-secret", "default"]
            if any(p in self.SECRET_KEY.lower() for p in insecure_patterns):
                raise ValueError("In production, SECRET_KEY cannot use default or placeholder values.")

            # 2. ENCRYPTION_MASTER_KEY validation
            if not self.ENCRYPTION_MASTER_KEY:
                raise ValueError("In production, ENCRYPTION_MASTER_KEY must be provided.")
            try:
                decoded = base64.b64decode(self.ENCRYPTION_MASTER_KEY)
                if len(decoded) != 32:
                    raise ValueError(f"Decoded key length must be exactly 32 bytes, got {len(decoded)}.")
            except Exception as e:
                raise ValueError(f"In production, ENCRYPTION_MASTER_KEY must be a valid 32-byte Base64 key: {e}")

        return self


settings = Settings()

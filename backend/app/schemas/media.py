from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SignUploadRequest(BaseModel):
    folder: Optional[str] = Field(None, description="Optional subfolder within organization directory")
    resource_type: str = Field(default="image", pattern=r"^(image|video|raw)$")
    eager_transformation: Optional[str] = Field(None, description="Cloudinary eager transformation string")
    product_id: Optional[str] = Field(None, description="Product ID to associate upload with")


class SignUploadResponse(BaseModel):
    cloud_name: str
    api_key: str
    timestamp: int
    signature: str
    folder: str
    upload_url: str
    resource_type: str
    eager: Optional[str] = None


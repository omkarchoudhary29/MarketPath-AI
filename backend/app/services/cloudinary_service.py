import hashlib
import time
from typing import Any, Dict, Optional
import cloudinary
import cloudinary.uploader
from backend.app.core.config import settings
from backend.app.schemas.media import SignUploadResponse


def is_cloudinary_configured() -> bool:
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
        and not settings.CLOUDINARY_CLOUD_NAME.startswith("your_")
    )


def init_cloudinary():
    if is_cloudinary_configured():
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )


def generate_signed_upload(
    organization_id: str,
    folder: Optional[str] = None,
    resource_type: str = "image",
    eager_transformation: Optional[str] = None,
) -> SignUploadResponse:
    """Generates a secure, short-lived signed upload payload for browser direct upload."""
    timestamp = int(time.time())
    upload_folder = f"marketpath/{organization_id}"
    if folder:
        clean_subfolder = folder.strip("/")
        upload_folder = f"{upload_folder}/{clean_subfolder}"

    params_to_sign: Dict[str, Any] = {
        "folder": upload_folder,
        "timestamp": timestamp,
    }
    if eager_transformation:
        params_to_sign["eager"] = eager_transformation

    if is_cloudinary_configured():
        init_cloudinary()
        signature = cloudinary.utils.api_sign_request(
            params_to_sign,
            settings.CLOUDINARY_API_SECRET,
        )
        api_key = settings.CLOUDINARY_API_KEY or "dev-api-key"
        cloud_name = settings.CLOUDINARY_CLOUD_NAME or "dev-cloud"
        upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/{resource_type}/upload"
    else:
        # Deterministic HMAC/SHA256 signature for development/testing
        sorted_pairs = [f"{k}={v}" for k, v in sorted(params_to_sign.items())]
        to_hash = "&".join(sorted_pairs) + "dev_secret_key"
        signature = hashlib.sha1(to_hash.encode("utf-8")).hexdigest()
        api_key = "mock_cloudinary_api_key"
        cloud_name = "mock_marketpath_cloud"
        upload_url = "https://api.cloudinary.com/v1_1/mock_marketpath_cloud/image/upload"

    return SignUploadResponse(
        cloud_name=cloud_name,
        api_key=api_key,
        timestamp=timestamp,
        signature=signature,
        folder=upload_folder,
        upload_url=upload_url,
        resource_type=resource_type,
        eager=eager_transformation,
    )


def delete_remote_asset(public_id: str, resource_type: str = "image") -> bool:
    """Removes an asset from Cloudinary."""
    if not is_cloudinary_configured():
        return True  # Simulated success in development/testing

    try:
        init_cloudinary()
        res = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return res.get("result") in ["ok", "not found"]
    except Exception as e:
        # Log failure without leaking credentials
        print(f"Warning: Cloudinary remote deletion failed for {public_id}: {str(e)}")
        return False


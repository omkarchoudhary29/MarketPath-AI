from fastapi import APIRouter, Depends
from backend.app.core.deps import TenantContext, require_role
from backend.app.schemas.media import SignUploadRequest, SignUploadResponse
from backend.app.services.cloudinary_service import generate_signed_upload

router = APIRouter(prefix="/media", tags=["Cloudinary Media Management"])


@router.post("/sign-upload", response_model=SignUploadResponse)
async def get_signed_upload_signature(
    payload: SignUploadRequest,
    context: TenantContext = Depends(require_role(["marketer"])),
):
    """Generates a secure, short-lived signed upload token for Cloudinary direct browser uploads (Marketer+)."""
    subfolder = payload.folder
    if payload.product_id:
        subfolder = f"products/{payload.product_id}"

    return generate_signed_upload(
        organization_id=str(context.organization_id),
        folder=subfolder,
        resource_type=payload.resource_type,
        eager_transformation=payload.eager_transformation,
    )


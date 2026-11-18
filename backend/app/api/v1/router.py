from fastapi import APIRouter
from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.agency import router as agency_router
from backend.app.api.v1.ai_studio import router as ai_studio_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.billing import router as billing_router
from backend.app.api.v1.brand import router as brand_router
from backend.app.api.v1.calendar import router as calendar_router
from backend.app.api.v1.campaigns import router as campaigns_router
from backend.app.api.v1.consultations import router as consultations_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.integrations import router as integrations_router
from backend.app.api.v1.inventory import router as inventory_router
from backend.app.api.v1.media import router as media_router
from backend.app.api.v1.notifications import router as notifications_router
from backend.app.api.v1.orders import router as orders_router
from backend.app.api.v1.organizations import router as org_router
from backend.app.api.v1.products import router as products_router
from backend.app.api.v1.publishing import router as publishing_router
from backend.app.api.v1.services import router as services_router
from backend.app.api.v1.support import router as support_router
from backend.app.api.v1.team import router as team_router
from backend.app.api.v1.voice import router as voice_router
from backend.app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(org_router)
api_router.include_router(brand_router)
api_router.include_router(calendar_router)
api_router.include_router(team_router)
api_router.include_router(notifications_router)
api_router.include_router(products_router)
api_router.include_router(voice_router)
api_router.include_router(media_router)
api_router.include_router(ai_studio_router)
api_router.include_router(campaigns_router)
api_router.include_router(consultations_router)
api_router.include_router(analytics_router)
api_router.include_router(billing_router)
api_router.include_router(services_router)
api_router.include_router(agency_router)
api_router.include_router(admin_router)
api_router.include_router(orders_router, prefix="/orders", tags=["Orders"])
api_router.include_router(inventory_router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(support_router, prefix="/support", tags=["Support Bot"])
api_router.include_router(integrations_router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(publishing_router, prefix="/publishing", tags=["Publishing"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])

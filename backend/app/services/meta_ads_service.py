import datetime
import logging
from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.models.marketing import AdAccount, Campaign, CampaignCreative
from backend.app.schemas.marketing import ManualExecutionPack

logger = logging.getLogger(__name__)

def validate_meta_version(version: str, api_name: str = "Meta API") -> str:
    """Validates that a Meta API version is not expired (must be >= v21.0)."""
    clean_ver = (version or "").strip().lower()
    if not clean_ver.startswith("v"):
        clean_ver = f"v{clean_ver}"
    try:
        ver_num = float(clean_ver.lstrip("v"))
        if ver_num < 21.0:
            raise ValueError(
                f"{api_name} version '{version}' is expired or sunset. "
                "Minimum supported active version is v21.0 (current recommended: v26.0)."
            )
    except ValueError as e:
        if "expired" in str(e):
            raise
        raise ValueError(f"Invalid {api_name} version format: '{version}'")
    return clean_ver

def get_meta_graph_api_version() -> str:
    return validate_meta_version(getattr(settings, "META_GRAPH_API_VERSION", "v26.0"), "Meta Graph API")

def get_meta_marketing_api_version() -> str:
    return validate_meta_version(getattr(settings, "META_MARKETING_API_VERSION", "v26.0"), "Meta Marketing API")

META_GRAPH_API_VERSION = get_meta_graph_api_version()
META_MARKETING_API_VERSION = get_meta_marketing_api_version()
META_GRAPH_BASE_URL = f"https://graph.facebook.com/{META_GRAPH_API_VERSION}"
META_MARKETING_BASE_URL = f"https://graph.facebook.com/{META_MARKETING_API_VERSION}"


class MetaAdsService:
    """Connector for Meta Marketing API (Facebook & Instagram Ads).
    
    Handles ad account discovery, campaign validation, campaign submission,
    and automatic fallback to manual execution packs when API access is pending review.
    """

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or getattr(settings, "META_ADS_ACCESS_TOKEN", None)
        self.app_id = getattr(settings, "META_APP_ID", None)
        self.app_secret = getattr(settings, "META_APP_SECRET", None)

    def is_api_configured(self) -> bool:
        """Checks if Meta Ads API credentials and access token are properly configured."""
        return bool(
            self.access_token
            and not self.access_token.startswith("your_")
            and len(self.access_token) > 15
        )

    async def get_ad_accounts(self) -> List[Dict[str, Any]]:
        """Fetches accessible Meta Ad Accounts for the authenticated user/system user."""
        if not self.is_api_configured():
            logger.info("Meta Ads API not configured. Returning local/simulated account info.")
            return [
                {
                    "id": "act_mock_9812401",
                    "account_id": "9812401",
                    "name": "Aura Terra Living (Primary Ad Account)",
                    "currency": "INR",
                    "account_status": 1,  # 1 = ACTIVE in Meta
                    "is_live": False,
                    "status_note": "Awaiting Meta Business Manager Ads Management App Review",
                }
            ]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{META_GRAPH_BASE_URL}/me/adaccounts",
                    params={
                        "fields": "id,account_id,name,currency,account_status,amount_spent,balance",
                        "access_token": self.access_token,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    return data.get("data", [])
                else:
                    logger.warning(f"Meta Ads API returned {res.status_code}: {res.text}")
                    return []
        except Exception as e:
            logger.error(f"Failed to query Meta Ad Accounts: {e}")
            return []

    async def create_campaign(
        self,
        ad_account_id: str,
        campaign: Campaign,
        selected_creative: Optional[CampaignCreative] = None,
    ) -> Dict[str, Any]:
        """Submits a new campaign to Meta Marketing API if authorized, or generates a manual setup pack.
        
        Meta Objective Mapping:
        - awareness -> OUTCOME_AWARENESS
        - traffic -> OUTCOME_TRAFFIC
        - engagement -> OUTCOME_ENGAGEMENT
        - leads -> OUTCOME_LEADS
        - sales -> OUTCOME_SALES
        """
        # Map internal objective to Meta ODAX objective
        objective_map = {
            "awareness": "OUTCOME_AWARENESS",
            "traffic": "OUTCOME_TRAFFIC",
            "engagement": "OUTCOME_ENGAGEMENT",
            "leads": "OUTCOME_LEADS",
            "sales": "OUTCOME_SALES",
        }
        meta_objective = objective_map.get(campaign.objective, "OUTCOME_SALES")

        # Check if live execution is authorized and credentials present
        if not self.is_api_configured():
            logger.info(
                f"Live Meta Ads API credentials unavailable for campaign {campaign.id}. "
                "Generating structured manual execution setup pack."
            )
            manual_pack = self.generate_manual_setup_pack(campaign, selected_creative)
            return {
                "success": True,
                "mode": "manual_setup",
                "status": "ready_for_manual_setup",
                "remote_campaign_id": None,
                "manual_execution_pack": manual_pack.model_dump(mode="json"),
                "message": (
                    "Live Meta Ads API execution requires Meta Business Manager verification "
                    "and Ads Management Standard Access approval. Complete structured setup pack "
                    "has been generated for immediate manual launch in Meta Ads Manager."
                ),
            }

        # Format live API payload for Meta Marketing API
        clean_account_id = ad_account_id if ad_account_id.startswith("act_") else f"act_{ad_account_id}"
        daily_budget_cents = int(float(campaign.daily_budget_limit) * 100)  # Meta expects budget in cents/paise

        payload = {
            "name": f"MarketPath - {campaign.name}",
            "objective": meta_objective,
            "status": "PAUSED",  # Always launch in PAUSED state so seller can review in Ads Manager
            "special_ad_categories": "NONE",
            "daily_budget": daily_budget_cents,
            "access_token": self.access_token,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{META_MARKETING_BASE_URL}/{clean_account_id}/campaigns",
                    data=payload,
                )
                if res.status_code in (200, 201):
                    result = res.json()
                    remote_id = result.get("id")
                    logger.info(f"Successfully created Meta campaign {remote_id} for campaign {campaign.id}")
                    return {
                        "success": True,
                        "mode": "live_api",
                        "status": "active",
                        "remote_campaign_id": remote_id,
                        "raw_response": result,
                        "message": f"Campaign created in Meta Ads Manager (ID: {remote_id}) in PAUSED state for final verification.",
                    }
                else:
                    error_payload = res.json()
                    error_msg = error_payload.get("error", {}).get("message", res.text)
                    logger.error(f"Meta Ads API campaign creation failed: {error_msg}")
                    # Fallback to manual pack on permission or rate error
                    manual_pack = self.generate_manual_setup_pack(campaign, selected_creative)
                    return {
                        "success": False,
                        "mode": "fallback_manual",
                        "status": "ready_for_manual_setup",
                        "error": error_msg,
                        "manual_execution_pack": manual_pack.model_dump(mode="json"),
                        "message": f"Meta API returned: {error_msg}. Exportable manual setup pack generated.",
                    }
        except Exception as e:
            logger.error(f"Exception during Meta campaign creation: {e}")
            manual_pack = self.generate_manual_setup_pack(campaign, selected_creative)
            return {
                "success": False,
                "mode": "fallback_manual",
                "status": "ready_for_manual_setup",
                "error": str(e),
                "manual_execution_pack": manual_pack.model_dump(mode="json"),
                "message": f"Network or execution error: {str(e)}. Exportable manual setup pack generated.",
            }

    async def update_campaign_status(
        self,
        remote_campaign_id: str,
        status: str,  # ACTIVE, PAUSED, ARCHIVED
    ) -> bool:
        """Updates remote campaign status in Meta Ads Manager."""
        if not self.is_api_configured() or not remote_campaign_id:
            return True  # Local state updated in DB

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{META_MARKETING_BASE_URL}/{remote_campaign_id}",
                    data={
                        "status": status.upper(),
                        "access_token": self.access_token,
                    },
                )
                return res.status_code == 200
        except Exception as e:
            logger.error(f"Failed to update Meta campaign status: {e}")
            return False

    def generate_manual_setup_pack(
        self,
        campaign: Campaign,
        creative: Optional[CampaignCreative] = None,
    ) -> ManualExecutionPack:
        """Generates an exportable, step-by-step manual execution guide and assets for Meta Ads Manager."""
        headline = creative.headline if creative else "Artisanal Living Crafted with Care"
        primary_text = creative.primary_text if creative else (
            f"Discover mindful design with {campaign.name}. Sustainable, authentic home goods delivered across India."
        )
        cta = creative.cta_text if creative else (campaign.call_to_action or "Shop Now")
        media_url = creative.media_url if creative else "https://res.cloudinary.com/marketpath/image/upload/v1/samples/lifestyle.jpg"
        landing_page = campaign.landing_page_url or "https://auraterra.in"

        # Generate UTM tags
        utm_source = "meta_ads"
        utm_medium = "paid_social"
        utm_campaign = campaign.name.lower().replace(" ", "_")
        separator = "&" if "?" in landing_page else "?"
        utm_url = f"{landing_page}{separator}utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}&utm_content=v1"

        duration_days = 30
        if campaign.end_date and campaign.start_date:
            duration_days = max((campaign.end_date - campaign.start_date).days, 1)

        targeting_checklist = {
            "platform": "Meta Ads Manager (Facebook & Instagram)",
            "campaign_objective": campaign.objective.upper(),
            "special_ad_categories": "None (Unless housing, credit, or employment)",
            "geography": campaign.target_geography or "Pan-India (Tier 1 Metros Preferred)",
            "age_range": "24 - 45",
            "gender": "All",
            "detailed_targeting_suggestions": [
                "Interiors & Home Decor",
                "Artisanal Crafts / Studio Pottery",
                "Sustainable Living",
                "Online Shopping / Premium D2C",
            ],
            "placements": "Advantage+ Placements (Automatic Feeds, Stories & Reels)",
        }

        budget_and_schedule = {
            "daily_budget": f"₹{float(campaign.daily_budget_limit):,.2f}",
            "lifetime_budget_cap": f"₹{float(campaign.total_budget):,.2f}",
            "pacing_duration": f"{duration_days} Days",
            "start_date": str(campaign.start_date),
            "end_date": str(campaign.end_date) if campaign.end_date else "Continuous",
            "bid_strategy": "Highest Volume (Lowest Cost) - Recommended for initial learning phase",
        }

        copy_and_creatives = [
            {
                "creative_format": campaign.creative_format or "Single Image / Video Feed Ad",
                "headline": headline,
                "primary_text": primary_text,
                "call_to_action": cta,
                "media_asset_url": media_url,
                "destination_url": utm_url,
            }
        ]

        step_by_step_instructions = [
            "Step 1: Open Meta Ads Manager (adsmanager.facebook.com) and ensure your verified Ad Account is selected.",
            f"Step 2: Click the green '+ Create' button and choose the '{campaign.objective.capitalize()}' campaign objective.",
            f"Step 3: Name the campaign '{campaign.name}' and ensure Special Ad Categories is left as 'None'.",
            f"Step 4: At the Ad Set level, set your Daily Budget to ₹{float(campaign.daily_budget_limit):,.2f} and schedule dates ({campaign.start_date} to {campaign.end_date or 'Ongoing'}).",
            f"Step 5: Set Location targeting to '{campaign.target_geography or 'India'}' and apply suggested interest tags.",
            "Step 6: At the Ad level, link your Facebook Page and Instagram Account.",
            f"Step 7: Upload the media asset from '{media_url}', paste the Headline and Primary Text provided above.",
            f"Step 8: Set the Website URL to your UTM-tagged destination: '{utm_url}'.",
            f"Step 9: Set Call to Action button to '{cta}'.",
            "Step 10: Verify Meta Pixel tracking is selected and click 'Publish' to enter Meta ad review.",
        ]

        return ManualExecutionPack(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            channel=campaign.channel,
            objective=campaign.objective,
            target_geography=campaign.target_geography or "Pan-India",
            targeting_checklist=targeting_checklist,
            budget_and_schedule=budget_and_schedule,
            copy_and_creatives=copy_and_creatives,
            utm_tagged_destination_url=utm_url,
            step_by_step_instructions=step_by_step_instructions,
            setup_status="Ready for Manual Setup",
        )

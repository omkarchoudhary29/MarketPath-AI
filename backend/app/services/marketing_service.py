import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.audit import AuditLog
from backend.app.models.brand import BrandProfile
from backend.app.models.catalogue import Product
from backend.app.models.marketing import (
    AdAccount,
    Campaign,
    CampaignCreative,
    CampaignMetricsDaily,
    ExternalCampaign,
)
from backend.app.models.user import UserProfile
from backend.app.schemas.marketing import (
    CampaignApprovalRequest,
    CampaignCreate,
    CampaignMetricsRead,
    CampaignPerformanceSummary,
    CampaignRead,
    CampaignUpdate,
    ManualExecutionPack,
)
from backend.app.services.campaign_planner_service import generate_campaign_plan
from backend.app.services.meta_ads_service import MetaAdsService

logger = logging.getLogger(__name__)


class CampaignNotFoundError(Exception):
    """Raised when a campaign is not found within the active organization."""
    pass


class MarketingService:
    """Core domain service for Marketing Studio, Campaign Planning & Advertising Execution."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.meta_ads_service = MetaAdsService()

    async def list_campaigns(
        self,
        organization_id: uuid.UUID,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Campaign]:
        """Lists campaigns belonging to the active organization with optional filters."""
        stmt = (
            select(Campaign)
            .where(Campaign.organization_id == organization_id)
            .options(selectinload(Campaign.creatives), selectinload(Campaign.product))
            .order_by(desc(Campaign.created_at))
        )

        if status and status != "all":
            stmt = stmt.where(Campaign.status == status)
        if channel and channel != "all":
            stmt = stmt.where(Campaign.channel == channel)
        if search:
            stmt = stmt.where(Campaign.name.ilike(f"%{search}%"))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_campaign(
        self,
        campaign_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> Optional[Campaign]:
        """Fetches a single campaign by ID ensuring tenant isolation."""
        stmt = (
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.organization_id == organization_id)
            .options(
                selectinload(Campaign.creatives),
                selectinload(Campaign.product),
                selectinload(Campaign.external_deployments).selectinload(ExternalCampaign.daily_metrics),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_campaign(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: CampaignCreate,
    ) -> Campaign:
        """Validates and creates a new marketing campaign brief."""
        # Budget and date range validations
        if payload.end_date and payload.start_date > payload.end_date:
            raise ValueError("Campaign start date cannot be after end date.")
        if payload.total_budget < payload.daily_budget_limit:
            raise ValueError("Total campaign budget must be greater than or equal to daily budget limit.")

        campaign = Campaign(
            organization_id=organization_id,
            product_id=payload.product_id,
            name=payload.name,
            objective=payload.objective,
            channel=payload.channel,
            target_geography=payload.target_geography or "Pan-India",
            target_audience_brief=payload.target_audience_brief,
            landing_page_url=payload.landing_page_url,
            call_to_action=payload.call_to_action or "Shop Now",
            creative_format=payload.creative_format or "feed_image",
            description=payload.description,
            total_budget=payload.total_budget,
            daily_budget_limit=payload.daily_budget_limit,
            currency=payload.currency,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status="draft",
            utm_params=payload.utm_params or {},
            ai_proposal=payload.ai_proposal,
        )
        self.db.add(campaign)
        await self.db.flush()

        # Add initial creatives if supplied
        if payload.creatives:
            for c_in in payload.creatives:
                creative = CampaignCreative(
                    campaign_id=campaign.id,
                    headline=c_in.headline,
                    primary_text=c_in.primary_text,
                    description_text=c_in.description_text,
                    cta_text=c_in.cta_text,
                    media_url=c_in.media_url,
                    destination_url=c_in.destination_url,
                    format=c_in.format,
                    version_number=c_in.version_number,
                    is_selected=c_in.is_selected,
                    is_approved=c_in.is_approved,
                )
                self.db.add(creative)

        # Audit log entry
        audit = AuditLog(
            organization_id=organization_id,
            actor_user_id=user_id,
            action="CAMPAIGN_CREATED",
            resource_type="campaign",
            resource_id=str(campaign.id),
            metadata_json={
                "campaign_name": campaign.name,
                "objective": campaign.objective,
                "channel": campaign.channel,
                "total_budget": float(campaign.total_budget),
                "daily_budget_limit": float(campaign.daily_budget_limit),
            },
        )
        self.db.add(audit)
        await self.db.commit()

        return await self.get_campaign(campaign.id, organization_id)

    async def update_campaign(
        self,
        campaign_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: CampaignUpdate,
    ) -> Campaign:
        """Updates an existing campaign brief (only if not yet live/completed)."""
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise CampaignNotFoundError("Campaign not found.")

        if campaign.status in ("completed", "archived"):
            raise ValueError(f"Cannot edit campaign in '{campaign.status}' state.")

        update_data = payload.model_dump(exclude_unset=True)

        # Validate budget if updated
        new_total = update_data.get("total_budget", float(campaign.total_budget))
        new_daily = update_data.get("daily_budget_limit", float(campaign.daily_budget_limit))
        if new_total < new_daily:
            raise ValueError("Total campaign budget must be greater than or equal to daily budget limit.")

        new_start = update_data.get("start_date", campaign.start_date)
        new_end = update_data.get("end_date", campaign.end_date)
        if new_end and new_start > new_end:
            raise ValueError("Start date cannot be after end date.")

        for field, value in update_data.items():
            setattr(campaign, field, value)

        audit = AuditLog(
            organization_id=organization_id,
            actor_user_id=user_id,
            action="CAMPAIGN_UPDATED",
            resource_type="campaign",
            resource_id=str(campaign.id),
            metadata_json={"updated_fields": list(update_data.keys())},
        )
        self.db.add(audit)
        await self.db.commit()

        return await self.get_campaign(campaign.id, organization_id)

    async def approve_campaign_budget(
        self,
        campaign_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        approval_req: CampaignApprovalRequest,
    ) -> Tuple[Campaign, ManualExecutionPack]:
        """Mandatory Human-In-The-Loop approval of campaign budget and targeting by owner/admin."""
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise CampaignNotFoundError("Campaign not found.")

        if not approval_req.approved:
            campaign.status = "draft"
            campaign.rejection_reason = approval_req.notes or "Rejected by reviewer."
            await self.db.commit()
            return campaign, None

        # Verify budget limits
        if float(campaign.total_budget) <= 0 or float(campaign.daily_budget_limit) <= 0:
            raise ValueError("Invalid campaign budget parameters.")

        campaign.approved_by_user_id = user_id
        campaign.approved_at = datetime.datetime.now(datetime.timezone.utc)

        # Get primary creative
        selected_creative = next((c for c in campaign.creatives if c.is_selected), None)
        if not selected_creative and campaign.creatives:
            selected_creative = campaign.creatives[0]

        # Generate structured manual execution pack
        manual_pack = self.meta_ads_service.generate_manual_setup_pack(campaign, selected_creative)
        campaign.manual_setup_instructions = manual_pack.model_dump(mode="json")
        campaign.status = "ready_for_manual_setup"

        # Log audit event
        audit = AuditLog(
            organization_id=organization_id,
            actor_user_id=user_id,
            action="CAMPAIGN_BUDGET_APPROVED",
            resource_type="campaign",
            resource_id=str(campaign.id),
            metadata_json={
                "approved_total_budget": float(campaign.total_budget),
                "approved_daily_limit": float(campaign.daily_budget_limit),
                "currency": campaign.currency,
                "notes": approval_req.notes,
            },
        )
        self.db.add(audit)
        await self.db.commit()

        return campaign, manual_pack

    async def launch_campaign(
        self,
        campaign_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        ad_account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes live campaign launch via Meta Ads API if authorized, or prepares manual setup pack."""
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise CampaignNotFoundError("Campaign not found.")

        if not campaign.approved_at or not campaign.approved_by_user_id:
            raise ValueError("Campaign requires explicit seller budget approval before launch.")

        selected_creative = next((c for c in campaign.creatives if c.is_selected), None)
        target_ad_account = ad_account_id or "act_primary"

        # Call Meta Ads Service
        result = await self.meta_ads_service.create_campaign(
            ad_account_id=target_ad_account,
            campaign=campaign,
            selected_creative=selected_creative,
        )

        if result.get("mode") == "live_api" and result.get("remote_campaign_id"):
            campaign.status = "active"
            # Record external campaign
            # Check if ad_account record exists or create one
            stmt_acc = select(AdAccount).where(
                AdAccount.organization_id == organization_id,
                AdAccount.external_account_id == target_ad_account,
            )
            acc_res = await self.db.execute(stmt_acc)
            ad_acc = acc_res.scalar_one_or_none()
            if not ad_acc:
                ad_acc = AdAccount(
                    organization_id=organization_id,
                    platform=campaign.channel,
                    external_account_id=target_ad_account,
                    account_name="Connected Ad Account",
                    currency=campaign.currency,
                    status="connected",
                )
                self.db.add(ad_acc)
                await self.db.flush()

            ext_campaign = ExternalCampaign(
                campaign_id=campaign.id,
                ad_account_id=ad_acc.id,
                platform=campaign.channel,
                remote_campaign_id=result["remote_campaign_id"],
                remote_status="ACTIVE",
                last_synced_at=datetime.datetime.now(datetime.timezone.utc),
            )
            self.db.add(ext_campaign)
        else:
            campaign.status = "ready_for_manual_setup"
            if result.get("manual_execution_pack"):
                campaign.manual_setup_instructions = result["manual_execution_pack"]

        audit = AuditLog(
            organization_id=organization_id,
            actor_user_id=user_id,
            action="CAMPAIGN_LAUNCHED",
            resource_type="campaign",
            resource_id=str(campaign.id),
            metadata_json={
                "mode": result.get("mode"),
                "status": campaign.status,
                "remote_campaign_id": result.get("remote_campaign_id"),
            },
        )
        self.db.add(audit)
        await self.db.commit()

        return result

    async def pause_campaign(
        self,
        campaign_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> Campaign:
        """Halts campaign ad spend immediately."""
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise CampaignNotFoundError("Campaign not found.")

        # Update external campaigns if deployed
        for ext in campaign.external_deployments:
            await self.meta_ads_service.update_campaign_status(ext.remote_campaign_id, "PAUSED")
            ext.remote_status = "PAUSED"

        campaign.status = "paused"

        audit = AuditLog(
            organization_id=organization_id,
            actor_user_id=user_id,
            action="CAMPAIGN_PAUSED",
            resource_type="campaign",
            resource_id=str(campaign.id),
            metadata_json={"reason": reason or "User requested pause"},
        )
        self.db.add(audit)
        await self.db.commit()

        return campaign

    async def resume_campaign(
        self,
        campaign_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Campaign:
        """Resumes active spend for an approved, paused campaign."""
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise CampaignNotFoundError("Campaign not found.")

        if not campaign.approved_at:
            raise ValueError("Cannot resume campaign without budget approval.")

        for ext in campaign.external_deployments:
            await self.meta_ads_service.update_campaign_status(ext.remote_campaign_id, "ACTIVE")
            ext.remote_status = "ACTIVE"

        campaign.status = "active" if campaign.external_deployments else "ready_for_manual_setup"

        audit = AuditLog(
            organization_id=organization_id,
            actor_user_id=user_id,
            action="CAMPAIGN_RESUMED",
            resource_type="campaign",
            resource_id=str(campaign.id),
            metadata_json={},
        )
        self.db.add(audit)
        await self.db.commit()

        return campaign

    async def stop_campaign(
        self,
        campaign_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> Campaign:
        """Permanently completes/stops campaign ad spend."""
        campaign = await self.get_campaign(campaign_id, organization_id)
        if not campaign:
            raise CampaignNotFoundError("Campaign not found.")

        for ext in campaign.external_deployments:
            await self.meta_ads_service.update_campaign_status(ext.remote_campaign_id, "ARCHIVED")
            ext.remote_status = "ARCHIVED"

        campaign.status = "completed"

        audit = AuditLog(
            organization_id=organization_id,
            actor_user_id=user_id,
            action="CAMPAIGN_STOPPED",
            resource_type="campaign",
            resource_id=str(campaign.id),
            metadata_json={"reason": reason or "Campaign completed"},
        )
        self.db.add(audit)
        await self.db.commit()

        return campaign

    async def get_performance_summary(
        self,
        campaign: Campaign,
    ) -> CampaignPerformanceSummary:
        """Calculates deterministic performance metrics for a campaign."""
        total_spend = 0.0
        total_impressions = 0
        total_clicks = 0
        total_reach = 0
        total_conversions = 0
        total_conv_value = 0.0
        daily_breakdown: List[CampaignMetricsRead] = []
        last_synced_at = None

        # Aggregate daily metrics from external deployments
        for ext in campaign.external_deployments:
            for dm in ext.daily_metrics:
                spend_val = float(dm.spend)
                total_spend += spend_val
                total_impressions += dm.impressions
                total_clicks += dm.clicks
                total_reach += dm.reach or 0
                total_conversions += dm.conversions
                total_conv_value += float(dm.conversion_value)

                # Derive CTR & CPC
                ctr = (dm.clicks / dm.impressions * 100.0) if dm.impressions > 0 else 0.0
                cpc = (spend_val / dm.clicks) if dm.clicks > 0 else 0.0
                roas = (float(dm.conversion_value) / spend_val) if spend_val > 0 else None

                daily_breakdown.append(
                    CampaignMetricsRead(
                        date=dm.date,
                        spend=spend_val,
                        impressions=dm.impressions,
                        clicks=dm.clicks,
                        reach=dm.reach or 0,
                        conversions=dm.conversions,
                        conversion_value=float(dm.conversion_value),
                        ctr=round(ctr, 2),
                        cpc=round(cpc, 2),
                        roas=round(roas, 2) if roas else None,
                        synced_at=dm.synced_at,
                    )
                )
                if not last_synced_at or dm.synced_at > last_synced_at:
                    last_synced_at = dm.synced_at

        # Calculate averages
        avg_ctr = (total_clicks / total_impressions * 100.0) if total_impressions > 0 else 0.0
        avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0.0
        blended_roas = (total_conv_value / total_spend) if total_spend > 0 else None
        remaining_budget = max(float(campaign.total_budget) - total_spend, 0.0)

        data_source = "Meta Marketing API" if campaign.external_deployments else "Manual / Not Connected"

        return CampaignPerformanceSummary(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            status=campaign.status,
            currency=campaign.currency,
            total_spend=round(total_spend, 2),
            total_budget=round(float(campaign.total_budget), 2),
            remaining_budget=round(remaining_budget, 2),
            daily_budget_limit=round(float(campaign.daily_budget_limit), 2),
            total_impressions=total_impressions,
            total_clicks=total_clicks,
            total_reach=total_reach,
            total_conversions=total_conversions,
            total_conversion_value=round(total_conv_value, 2),
            average_ctr=round(avg_ctr, 2),
            average_cpc=round(avg_cpc, 2),
            blended_roas=round(blended_roas, 2) if blended_roas else None,
            data_source=data_source,
            attribution_window="7-day click / 1-day view",
            last_synced_at=last_synced_at,
            daily_breakdown=daily_breakdown,
        )

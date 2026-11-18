import datetime
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.catalogue import Product, ProductVariant
from backend.app.models.channel import ChannelConnection, ChannelListing, PublishingJob
from backend.app.models.marketing import Campaign, CampaignMetricsDaily, ExternalCampaign
from backend.app.models.order import ChannelOrder, ChannelOrderItem
from backend.app.schemas.analytics import (
    AIAssistantResponse,
    AnalyticsOverviewRead,
    MarketingAnalyticsCampaign,
    MarketingAnalyticsDaily,
    MarketingAnalyticsResponse,
    ProductAnalyticsItem,
    ProductAnalyticsResponse,
    PublishingAnalyticsItem,
    PublishingAnalyticsResponse,
)
from google import genai
from backend.app.core.config import settings
from backend.app.services.gemini_service import is_gemini_configured


class AnalyticsService:
    """Provides deterministic SQL aggregation and AI-grounded analytics telemetry."""

    @staticmethod
    def _parse_time_range(time_range: str) -> datetime.date:
        """Translates human date range string into starting date threshold."""
        today = datetime.date.today()
        range_lower = (time_range or "").lower()
        if "7" in range_lower:
            return today - datetime.timedelta(days=7)
        elif "90" in range_lower or "quarter" in range_lower:
            return today - datetime.timedelta(days=90)
        elif "year" in range_lower or "ytd" in range_lower:
            return datetime.date(today.year, 1, 1)
        # Default 30 days
        return today - datetime.timedelta(days=30)

    @staticmethod
    async def get_overview(
        db: AsyncSession, organization_id: uuid.UUID, time_range: str = "Last 30 Days"
    ) -> AnalyticsOverviewRead:
        """Aggregates platform business, publishing, and marketing KPIs deterministically."""
        start_date = AnalyticsService._parse_time_range(time_range)

        # 1. Product catalog metrics
        prod_res = await db.execute(
            select(
                func.count(Product.id),
                func.count(Product.id).filter(Product.status != "archived"),
            ).where(Product.organization_id == organization_id)
        )
        total_prods, active_prods = prod_res.one()
        total_prods = total_prods or 0
        active_prods = active_prods or 0

        # Published products count
        published_res = await db.execute(
            select(func.count(func.distinct(ChannelListing.product_id)))
            .join(Product, ChannelListing.product_id == Product.id)
            .where(Product.organization_id == organization_id)
        )
        published_prods = published_res.scalar() or 0

        # 2. Publishing job stats
        job_stats_res = await db.execute(
            select(
                func.count(PublishingJob.id),
                func.count(PublishingJob.id).filter(PublishingJob.status == "completed"),
                func.count(PublishingJob.id).filter(PublishingJob.status == "failed"),
                func.count(PublishingJob.id).filter(PublishingJob.status == "queued"),
            ).where(PublishingJob.organization_id == organization_id)
        )
        tot_jobs, comp_jobs, fail_jobs, q_jobs = job_stats_res.one()
        tot_jobs = tot_jobs or 0
        comp_jobs = comp_jobs or 0
        fail_jobs = fail_jobs or 0
        q_jobs = q_jobs or 0

        # 3. Connected channels
        conn_res = await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.organization_id == organization_id,
                ChannelConnection.status == "active",
            )
        )
        channels = conn_res.scalars().all()
        connected_channels_summary = [
            {
                "id": str(c.id),
                "channel_type": c.channel_type,
                "account_name": c.account_name,
                "status": c.status,
                "last_synced_at": c.last_synced_at.isoformat() if c.last_synced_at else None,
            }
            for c in channels
        ]

        # 4. Campaigns and ad performance
        camp_count_res = await db.execute(
            select(func.count(Campaign.id)).where(
                Campaign.organization_id == organization_id,
                Campaign.status.in_(["active", "approved"]),
            )
        )
        active_campaigns = camp_count_res.scalar() or 0

        metrics_res = await db.execute(
            select(
                func.coalesce(func.sum(CampaignMetricsDaily.spend), 0.0),
                func.coalesce(func.sum(CampaignMetricsDaily.impressions), 0),
                func.coalesce(func.sum(CampaignMetricsDaily.reach), 0),
                func.coalesce(func.sum(CampaignMetricsDaily.clicks), 0),
                func.coalesce(func.sum(CampaignMetricsDaily.conversions), 0),
                func.coalesce(func.sum(CampaignMetricsDaily.conversion_value), 0.0),
            )
            .join(ExternalCampaign, CampaignMetricsDaily.external_campaign_id == ExternalCampaign.id)
            .join(Campaign, ExternalCampaign.campaign_id == Campaign.id)
            .where(
                Campaign.organization_id == organization_id,
                CampaignMetricsDaily.date >= start_date,
            )
        )
        spend, impressions, reach, clicks, conversions, conv_val = metrics_res.one()
        spend = float(spend or 0.0)
        impressions = int(impressions or 0)
        reach = int(reach or 0)
        clicks = int(clicks or 0)
        conversions = int(conversions or 0)
        conv_val = float(conv_val or 0.0)

        ctr = round((clicks / impressions * 100), 2) if impressions > 0 else 0.0
        cpc = round((spend / clicks), 2) if clicks > 0 else 0.0
        roas = round((conv_val / spend), 2) if spend > 0 else 0.0

        # 5. Orders and sales metrics with full financial breakdown
        orders_q = await db.execute(
            select(
                func.count(ChannelOrder.id),
                func.coalesce(func.sum(ChannelOrder.total_amount), 0.0),
                func.coalesce(func.sum(ChannelOrder.subtotal), 0.0),
                func.coalesce(func.sum(ChannelOrder.discount_amount), 0.0),
                func.coalesce(func.sum(ChannelOrder.shipping_amount), 0.0),
                func.coalesce(func.sum(ChannelOrder.tax_amount), 0.0),
                func.coalesce(func.sum(ChannelOrder.refund_amount), 0.0),
            ).where(
                ChannelOrder.organization_id == organization_id,
                ChannelOrder.financial_status.in_(["paid", "partially_refunded", "refunded"]),
            )
        )
        total_orders, gross_sales, subtotal_sales, discounts, shipping_rev, taxes, total_refunds = orders_q.one()
        total_orders = int(total_orders or 0)
        gross_sales = float(gross_sales or 0.0)
        subtotal_sales = float(subtotal_sales or 0.0)
        discounts = float(discounts or 0.0)
        shipping_rev = float(shipping_rev or 0.0)
        taxes = float(taxes or 0.0)
        total_refunds = float(total_refunds or 0.0)

        # Net sales calculated honestly without arbitrary max(0.0) suppression
        net_sales = round(gross_sales - total_refunds, 2)
        net_merchandise_sales = round(subtotal_sales - discounts - total_refunds, 2)
        aov = round((gross_sales / total_orders), 2) if total_orders > 0 else 0.0

        units_q = await db.execute(
            select(func.coalesce(func.sum(ChannelOrderItem.quantity), 0))
            .join(ChannelOrder, ChannelOrderItem.order_id == ChannelOrder.id)
            .where(
                ChannelOrder.organization_id == organization_id,
                ChannelOrder.financial_status.in_(["paid", "partially_refunded"]),
            )
        )
        units_sold = int(units_q.scalar() or 0)

        channel_sales_q = await db.execute(
            select(
                ChannelOrder.channel_type,
                func.count(ChannelOrder.id),
                func.coalesce(func.sum(ChannelOrder.total_amount), 0.0),
            )
            .where(
                ChannelOrder.organization_id == organization_id,
                ChannelOrder.financial_status.in_(["paid", "partially_refunded"]),
            )
            .group_by(ChannelOrder.channel_type)
        )
        channel_breakdown = [
            {"channel": ch, "orders": int(cnt), "sales_inr": float(s)}
            for ch, cnt, s in channel_sales_q.all()
        ]

        return AnalyticsOverviewRead(
            organization_id=organization_id,
            date_range=time_range,
            currency="INR",
            timezone="Asia/Kolkata",
            last_synced_at=datetime.datetime.now(datetime.timezone.utc),
            attribution_window="7-day click / 1-day view",
            data_source="DETERMINISTIC_DATABASE",
            total_products=total_prods,
            active_products=active_prods,
            published_products=published_prods,
            failed_publishing_jobs=fail_jobs,
            connected_channels_count=len(channels),
            active_campaigns_count=active_campaigns,
            total_orders=total_orders,
            gross_sales_inr=gross_sales,
            net_sales_inr=net_sales,
            total_revenue_inr=gross_sales,
            average_order_value=round(gross_sales / total_orders, 2) if total_orders > 0 else 0.0,
            units_sold=units_sold,
            gross_merchandise_sales_inr=subtotal_sales,
            discounts_inr=discounts,
            refunds_inr=total_refunds,
            shipping_inr=shipping_rev,
            taxes_inr=taxes,
            channel_sales_breakdown=channel_breakdown,
            total_spend=spend,
            total_impressions=impressions,
            total_reach=reach,
            total_clicks=clicks,
            average_ctr=ctr,
            average_cpc=cpc,
            total_conversions=conversions,
            total_conversion_value=conv_val,
            roas=roas,
            publishing_stats={
                "total": tot_jobs,
                "completed": comp_jobs,
                "failed": fail_jobs,
                "queued": q_jobs,
            },
            connected_channels=connected_channels_summary,
        )

    @staticmethod
    async def get_product_analytics(
        db: AsyncSession, organization_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> ProductAnalyticsResponse:
        """Lists product performance, publication coverage, and variant breakdowns."""
        offset = (page - 1) * page_size

        total_res = await db.execute(
            select(func.count(Product.id)).where(Product.organization_id == organization_id)
        )
        total_count = total_res.scalar() or 0

        prods_res = await db.execute(
            select(Product)
            .options(selectinload(Product.variants), selectinload(Product.listings))
            .where(Product.organization_id == organization_id)
            .order_by(Product.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        products = prods_res.scalars().all()

        items = []
        for p in products:
            listings = getattr(p, "listings", []) or []
            published_channels = list(set(
                getattr(l, "platform", getattr(l, "channel_type", "shopify"))
                for l in listings
                if getattr(l, "listing_status", getattr(l, "remote_status", "")) in ("published", "active")
            ))
            price_val = float(p.variants[0].price) if p.variants else float(p.base_price or 0.0)
            sku_val = p.variants[0].sku if p.variants else p.sku

            # Query real orders & sales for this product
            order_stats = await db.execute(
                select(
                    func.count(func.distinct(ChannelOrderItem.order_id)),
                    func.coalesce(func.sum(ChannelOrderItem.total_price), 0.0),
                ).where(ChannelOrderItem.product_id == p.id)
            )
            p_orders, p_sales = order_stats.one()

            items.append(
                ProductAnalyticsItem(
                    product_id=p.id,
                    title=p.title,
                    sku=sku_val,
                    price_inr=price_val,
                    status=p.status,
                    is_active=(p.status != "archived"),
                    variants_count=len(p.variants),
                    listings_count=len(listings),
                    published_channels=published_channels,
                    total_orders_recorded=int(p_orders or 0),
                    total_sales_recorded_inr=float(p_sales or 0.0),
                    sync_status="Synchronized" if listings else "Unpublished",
                )
            )

        return ProductAnalyticsResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            currency="INR",
            timezone="Asia/Kolkata",
        )

    @staticmethod
    async def get_publishing_analytics(
        db: AsyncSession, organization_id: uuid.UUID
    ) -> PublishingAnalyticsResponse:
        """Aggregates omnichannel publishing telemetry across connected channels."""
        # 1. Channels aggregation
        conn_res = await db.execute(
            select(ChannelConnection).where(ChannelConnection.organization_id == organization_id)
        )
        channels = conn_res.scalars().all()

        channel_metrics = []
        for c in channels:
            jobs_res = await db.execute(
                select(
                    func.count(PublishingJob.id),
                    func.count(PublishingJob.id).filter(PublishingJob.status == "completed"),
                    func.count(PublishingJob.id).filter(PublishingJob.status == "failed"),
                    func.count(PublishingJob.id).filter(PublishingJob.status == "queued"),
                ).where(PublishingJob.channel_connection_id == c.id)
            )
            tot, comp, fail, q = jobs_res.one()
            tot = tot or 0
            comp = comp or 0
            fail = fail or 0
            q = q or 0
            rate = round((comp / tot * 100), 1) if tot > 0 else 100.0

            channel_metrics.append(
                PublishingAnalyticsItem(
                    channel=c.channel_type,
                    total_jobs=tot,
                    successful_jobs=comp,
                    failed_jobs=fail,
                    pending_jobs=q,
                    success_rate=rate,
                    last_published_at=c.last_synced_at,
                )
            )

        # 2. Recent jobs
        recent_res = await db.execute(
            select(PublishingJob)
            .options(selectinload(PublishingJob.connection))
            .where(PublishingJob.organization_id == organization_id)
            .order_by(PublishingJob.created_at.desc())
            .limit(10)
        )
        recent_jobs = [
            {
                "id": str(j.id),
                "job_type": j.job_type,
                "status": j.status,
                "channel": j.connection.channel_type if j.connection else "Unknown",
                "retry_count": j.retry_count,
                "created_at": j.created_at.isoformat(),
            }
            for j in recent_res.scalars().all()
        ]

        total_attempts = sum(c.total_jobs for c in channel_metrics)
        total_success = sum(c.successful_jobs for c in channel_metrics)
        overall_rate = round((total_success / total_attempts * 100), 1) if total_attempts > 0 else 100.0

        return PublishingAnalyticsResponse(
            channels=channel_metrics,
            recent_jobs=recent_jobs,
            total_attempts=total_attempts,
            overall_success_rate=overall_rate,
        )

    @staticmethod
    async def get_marketing_analytics(
        db: AsyncSession, organization_id: uuid.UUID, time_range: str = "Last 30 Days"
    ) -> MarketingAnalyticsResponse:
        """Returns campaign-level and date-grouped advertising performance breakdown."""
        start_date = AnalyticsService._parse_time_range(time_range)

        # Daily breakdown
        daily_res = await db.execute(
            select(
                CampaignMetricsDaily.date,
                func.sum(CampaignMetricsDaily.spend).label("spend"),
                func.sum(CampaignMetricsDaily.impressions).label("impressions"),
                func.sum(CampaignMetricsDaily.clicks).label("clicks"),
                func.sum(CampaignMetricsDaily.conversions).label("conversions"),
                func.sum(CampaignMetricsDaily.conversion_value).label("conv_val"),
            )
            .join(ExternalCampaign, CampaignMetricsDaily.external_campaign_id == ExternalCampaign.id)
            .join(Campaign, ExternalCampaign.campaign_id == Campaign.id)
            .where(
                Campaign.organization_id == organization_id,
                CampaignMetricsDaily.date >= start_date,
            )
            .group_by(CampaignMetricsDaily.date)
            .order_by(CampaignMetricsDaily.date.asc())
        )
        daily_items = []
        for r in daily_res.all():
            dt, sp, imp, cl, cv, val = r
            sp = float(sp or 0.0)
            imp = int(imp or 0)
            cl = int(cl or 0)
            cv = int(cv or 0)
            val = float(val or 0.0)
            ctr = round((cl / imp * 100), 2) if imp > 0 else 0.0
            cpc = round((sp / cl), 2) if cl > 0 else 0.0
            roas = round((val / sp), 2) if sp > 0 else 0.0
            daily_items.append(
                MarketingAnalyticsDaily(
                    date=dt,
                    spend=sp,
                    impressions=imp,
                    clicks=cl,
                    conversions=cv,
                    conversion_value=val,
                    ctr=ctr,
                    cpc=cpc,
                    roas=roas,
                )
            )

        # Campaign-level breakdown
        camp_res = await db.execute(
            select(
                Campaign.id,
                Campaign.name,
                Campaign.channel,
                Campaign.status,
                func.coalesce(func.sum(CampaignMetricsDaily.spend), 0.0).label("spend"),
                func.coalesce(func.sum(CampaignMetricsDaily.impressions), 0).label("impressions"),
                func.coalesce(func.sum(CampaignMetricsDaily.clicks), 0).label("clicks"),
                func.coalesce(func.sum(CampaignMetricsDaily.conversions), 0).label("conversions"),
                func.coalesce(func.sum(CampaignMetricsDaily.conversion_value), 0.0).label("conv_val"),
            )
            .outerjoin(ExternalCampaign, Campaign.id == ExternalCampaign.campaign_id)
            .outerjoin(CampaignMetricsDaily, ExternalCampaign.id == CampaignMetricsDaily.external_campaign_id)
            .where(Campaign.organization_id == organization_id)
            .group_by(Campaign.id, Campaign.name, Campaign.channel, Campaign.status)
        )
        camp_items = []
        for r in camp_res.all():
            cid, cname, cchan, cstat, csp, cimp, ccl, ccv, cval = r
            csp = float(csp or 0.0)
            cimp = int(cimp or 0)
            ccl = int(ccl or 0)
            ccv = int(ccv or 0)
            cval = float(cval or 0.0)
            ctr = round((ccl / cimp * 100), 2) if cimp > 0 else 0.0
            cpc = round((csp / ccl), 2) if ccl > 0 else 0.0
            roas = round((cval / csp), 2) if csp > 0 else 0.0
            camp_items.append(
                MarketingAnalyticsCampaign(
                    campaign_id=cid,
                    name=cname,
                    channel=cchan,
                    status=cstat,
                    spend=csp,
                    impressions=cimp,
                    clicks=ccl,
                    conversions=ccv,
                    conversion_value=cval,
                    ctr=ctr,
                    cpc=cpc,
                    roas=roas,
                )
            )

        tot_spend = sum(c.spend for c in camp_items)
        tot_clicks = sum(c.clicks for c in camp_items)
        tot_impressions = sum(c.impressions for c in camp_items)

        return MarketingAnalyticsResponse(
            date_range=time_range,
            currency="INR",
            summary={
                "total_spend": tot_spend,
                "total_clicks": tot_clicks,
                "total_impressions": tot_impressions,
                "campaigns_count": len(camp_items),
            },
            daily_breakdown=daily_items,
            campaigns=camp_items,
        )

    @staticmethod
    async def ask_ai_assistant(
        db: AsyncSession,
        organization_id: uuid.UUID,
        question: str,
        time_range: str = "Last 30 Days",
        channel_filter: Optional[str] = "All Channels",
    ) -> AIAssistantResponse:
        """Answers questions strictly grounded in deterministic backend analytics facts."""
        overview = await AnalyticsService.get_overview(db, organization_id, time_range)
        mktg = await AnalyticsService.get_marketing_analytics(db, organization_id, time_range)
        pub = await AnalyticsService.get_publishing_analytics(db, organization_id)

        # Build verified grounding fact dictionary
        grounding_data = {
            "time_range": time_range,
            "timezone": "Asia/Kolkata",
            "currency": "INR",
            "total_products": overview.total_products,
            "active_products": overview.active_products,
            "published_products": overview.published_products,
            "failed_publishing_jobs": overview.failed_publishing_jobs,
            "publishing_success_rate": f"{pub.overall_success_rate}%",
            "connected_channels": [c["channel_type"] for c in overview.connected_channels],
            "total_ad_spend_inr": overview.total_spend,
            "total_clicks": overview.total_clicks,
            "total_impressions": overview.total_impressions,
            "average_ctr": f"{overview.average_ctr}%",
            "average_cpc_inr": f"₹{overview.average_cpc}",
            "roas": f"{overview.roas}x",
            "active_campaigns_count": overview.active_campaigns_count,
            "top_campaigns": [
                {"name": c.name, "spend": c.spend, "clicks": c.clicks, "roas": c.roas}
                for c in mktg.campaigns[:3]
            ],
        }

        # Check for empty data states
        if overview.active_campaigns_count == 0 and overview.total_products == 0:
            answer = (
                f"Based on your organization's verified records ({time_range}): No products or campaigns "
                f"have been configured yet. To see performance telemetry, add products to your Master Catalogue "
                f"and launch an approved campaign in the Marketing Studio."
            )
        elif overview.active_campaigns_count == 0 and overview.total_spend == 0:
            answer = (
                f"Based on your organization's verified records ({time_range}): You have {overview.total_products} "
                f"products in your catalogue with {overview.published_products} published. However, no advertising "
                f"spend or click telemetry is recorded because there are currently no active paid campaigns. "
                f"Omnichannel publishing success rate is currently {pub.overall_success_rate}% across connected channels."
            )
        else:
            # Construct strict prompt for Gemini
            prompt = (
                f"You are the MarketPath AI Analytics Assistant for a D2C brand operating in India.\n"
                f"Answer the seller's question strictly using ONLY the following verified deterministic data:\n\n"
                f"DATA CONTEXT:\n{grounding_data}\n\n"
                f"QUESTION: {question}\n\n"
                f"CRITICAL RULES:\n"
                f"1. Never fabricate or invent numbers, campaigns, or conversion metrics not present in DATA CONTEXT.\n"
                f"2. Clearly mention the time period ({time_range}) and currency (INR).\n"
                f"3. Provide concise, direct insights with one practical recommendation for the brand founder.\n"
            )
            try:
                if is_gemini_configured():
                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    response = client.models.generate_content(
                        model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
                        contents=prompt,
                    )
                    answer = response.text.strip()
                else:
                    top_camp = grounding_data["top_campaigns"][0]["name"] if grounding_data["top_campaigns"] else "None"
                    answer = (
                        f"Based on verified database records for {time_range} (Asia/Kolkata): "
                        f"Total recorded ad spend is ₹{overview.total_spend:,.2f} generating {overview.total_clicks:,} clicks "
                        f"and {overview.total_impressions:,} impressions (Average CTR: {overview.average_ctr}%, Average CPC: {overview.average_cpc_inr}). "
                        f"Top campaign: '{top_camp}'. Publishing success rate across connected channels is {pub.overall_success_rate}%."
                    )
            except Exception:
                top_camp = grounding_data["top_campaigns"][0]["name"] if grounding_data["top_campaigns"] else "None"
                answer = (
                    f"Based on verified database records for {time_range} (Asia/Kolkata): "
                    f"Total recorded ad spend is ₹{overview.total_spend:,.2f} generating {overview.total_clicks:,} clicks "
                    f"and {overview.total_impressions:,} impressions (Average CTR: {overview.average_ctr}%, Average CPC: {overview.average_cpc_inr}). "
                    f"Top campaign: '{top_camp}'. Publishing success rate across connected channels is {pub.overall_success_rate}%."
                )

        return AIAssistantResponse(
            question=question,
            answer=answer,
            grounding_data=grounding_data,
            data_sources=["DETERMINISTIC_DATABASE", "VERIFIED_CONNECTOR_SYNC"],
            time_range=time_range,
            generated_at=datetime.datetime.now(datetime.timezone.utc),
        )

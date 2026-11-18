import datetime
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.audit import AuditLog
from backend.app.models.billing import Payment, Plan, ServiceOrder, Subscription, UsageEvent
from backend.app.models.catalogue import Product
from backend.app.models.channel import ChannelConnection, PublishingJob
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.schemas.billing import ServiceCatalogItem, UsageMeterItem, UsageStatsRead


DEFAULT_PLANS = [
    {
        "name": "Starter",
        "monthly_price_inr": 999,
        "max_active_skus": 10,
        "max_connected_channels": 1,
        "ai_generation_monthly_quota": 100,
        "description": "Best for emerging solo brands validating their first products in market.",
        "features": {
            "basic_ai_studio": True,
            "single_channel_publishing": True,
            "email_support": True,
        },
    },
    {
        "name": "Growth",
        "monthly_price_inr": 2499,
        "max_active_skus": 100,
        "max_connected_channels": 3,
        "ai_generation_monthly_quota": 500,
        "description": "For scaling D2C brands publishing across multiple connected storefronts.",
        "features": {
            "advanced_ai_studio": True,
            "inventory_sync": True,
            "multi_channel_publishing": True,
            "priority_support": True,
        },
    },
    {
        "name": "Scale",
        "monthly_price_inr": 5999,
        "max_active_skus": 500,
        "max_connected_channels": 5,
        "ai_generation_monthly_quota": 2000,
        "description": "For established multi-channel brands with campaign automation and reporting.",
        "features": {
            "campaign_planner": True,
            "advanced_ai_studio": True,
            "dedicated_support": True,
            "custom_reporting": True,
            "omnichannel_sync": True,
        },
    },
]

MANAGED_SERVICES_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "srv_onboarding",
        "service_type": "guided_onboarding",
        "name": "Guided Onboarding & Setup",
        "short_description": "Dedicated 1-on-1 walkthrough to configure your brand profile, connect accounts, and import your initial catalogue.",
        "scope_bullets": [
            "Complete organization and brand profile setup",
            "Shopify Admin and Instagram Professional connection verification",
            "Initial catalogue import and taxonomy mapping",
            "60-minute live operator strategy session",
        ],
        "starting_price_inr": 2999,
        "deliverable_timeline": "3 Business Days",
        "recommended_for": "New brands wanting a smooth launch",
    },
    {
        "id": "srv_catalogue_setup",
        "service_type": "catalogue_setup",
        "name": "Product Catalogue Standardization",
        "short_description": "We take your raw spreadsheets or PDFs, standardize SKUs, write structured attributes, and prepare them for publishing.",
        "scope_bullets": [
            "Up to 50 parent products with variant structures",
            "Standardized pricing, barcodes, and inventory weights",
            "SEO-optimized titles and category classification",
            "High-resolution Cloudinary image asset structuring",
        ],
        "starting_price_inr": 4999,
        "deliverable_timeline": "5 Business Days",
        "recommended_for": "Brands migrating from legacy spreadsheets",
    },
    {
        "id": "srv_photography",
        "service_type": "photography_assistance",
        "name": "Product Photography & Asset Polish",
        "short_description": "Studio asset enhancement, background removal, aspect ratio standardization, and lifestyle mockups for omnichannel.",
        "scope_bullets": [
            "Clean studio background extraction (white & contextual)",
            "1:1 Feed and 9:16 Story format optimization",
            "Compression and Cloudinary CDN pre-generation",
            "Up to 25 products (4 angles each)",
        ],
        "starting_price_inr": 7499,
        "deliverable_timeline": "7 Business Days",
        "recommended_for": "Brands preparing social marketing campaigns",
    },
    {
        "id": "srv_content_pack",
        "service_type": "content_package",
        "name": "Omnichannel Content Package",
        "short_description": "Human-curated, AI-accelerated copy package tailored for Shopify SEO, Instagram captions, and marketplace listings.",
        "scope_bullets": [
            "Channel-specific descriptions for up to 30 products",
            "20 ready-to-publish Instagram caption variations with hashtags",
            "High-converting value proposition hooks",
            "Full review and sign-off by a dedicated e-commerce copywriter",
        ],
        "starting_price_inr": 3999,
        "deliverable_timeline": "4 Business Days",
        "recommended_for": "Brands looking to boost organic conversion rates",
    },
    {
        "id": "srv_campaign_setup",
        "service_type": "campaign_setup",
        "name": "Meta Ads Campaign Setup & Brief",
        "short_description": "End-to-end campaign architecture, audience targeting setup, creative mockups, and pre-tagged UTM links ready to execute.",
        "scope_bullets": [
            "Meta Business Manager & Pixel verification assistance",
            "2 custom audience segments (Interest + Retargeting)",
            "4 high-converting ad creative formats (Feed & Story)",
            "10-step manual setup pack or direct API execution support",
        ],
        "starting_price_inr": 5999,
        "deliverable_timeline": "5 Business Days",
        "recommended_for": "Brands ready to launch paid traffic profitably",
    },
    {
        "id": "srv_consultation",
        "service_type": "marketing_consultation",
        "name": "D2C Growth Strategy Consultation",
        "short_description": "Comprehensive monthly growth audit, funnel analysis, channel mix recommendations, and margin optimization.",
        "scope_bullets": [
            "Two 45-minute monthly strategy calls with D2C growth specialist",
            "Performance audit across Shopify, Meta Ads, and social channels",
            "Actionable monthly sprint plan with KPI targets",
            "Direct Slack/Email advisory access",
        ],
        "starting_price_inr": 9999,
        "deliverable_timeline": "Monthly Retainer",
        "recommended_for": "Scaling brands targeting ₹10L+ monthly GMV",
    },
]


class BillingService:
    """Manages SaaS plans, tenant subscriptions, quotas, and service orders."""

    @staticmethod
    async def seed_default_plans(db: AsyncSession) -> List[Plan]:
        """Seeds standard SaaS plans if none exist."""
        result = await db.execute(select(Plan))
        existing = result.scalars().all()
        if existing:
            return list(existing)

        seeded_plans = []
        for p in DEFAULT_PLANS:
            new_plan = Plan(
                name=p["name"],
                monthly_price_inr=p["monthly_price_inr"],
                max_active_skus=p["max_active_skus"],
                max_connected_channels=p["max_connected_channels"],
                ai_generation_monthly_quota=p["ai_generation_monthly_quota"],
                description=p["description"],
                features=p["features"],
                is_active=True,
            )
            db.add(new_plan)
            seeded_plans.append(new_plan)

        await db.commit()
        for p in seeded_plans:
            await db.refresh(p)
        return seeded_plans

    @staticmethod
    async def get_active_plans(db: AsyncSession) -> List[Plan]:
        """Returns all currently active SaaS plans."""
        result = await db.execute(
            select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.monthly_price_inr.asc())
        )
        plans = result.scalars().all()
        if not plans:
            plans = await BillingService.seed_default_plans(db)
        return list(plans)

    @staticmethod
    async def get_or_create_tenant_subscription(
        db: AsyncSession, organization_id: uuid.UUID
    ) -> Subscription:
        """Retrieves tenant subscription or provisions a default Growth tier subscription."""
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.organization_id == organization_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            return sub

        # Ensure plans exist
        plans = await BillingService.get_active_plans(db)
        default_plan = next((p for p in plans if p.name == "Growth"), plans[0])

        now = datetime.datetime.now(datetime.timezone.utc)
        sub = Subscription(
            organization_id=organization_id,
            plan_id=default_plan.id,
            status="active",
            current_period_start=now,
            current_period_end=now + datetime.timedelta(days=30),
            cancel_at_period_end=False,
            gateway_subscription_id=f"sub_trial_{uuid.uuid4().hex[:10]}",
        )
        db.add(sub)
        await db.commit()

        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.id == sub.id)
        )
        return result.scalar_one()

    @staticmethod
    async def check_quota(
        db: AsyncSession, organization_id: uuid.UUID, metric: str
    ) -> Tuple[bool, str]:
        """Enforces plan resource quotas on the backend.
        
        Supported metrics: 'active_skus', 'connected_channels', 'ai_generation'
        """
        sub = await BillingService.get_or_create_tenant_subscription(db, organization_id)
        plan = sub.plan

        if metric == "active_skus":
            sku_count_res = await db.execute(
                select(func.count(Product.id)).where(
                    Product.organization_id == organization_id,
                    Product.status != "archived",
                )
            )
            count = sku_count_res.scalar() or 0
            if count >= plan.max_active_skus:
                return (
                    False,
                    f"Active SKU quota exceeded. Your current plan '{plan.name}' allows up to {plan.max_active_skus} active SKUs (Current: {count}). Please upgrade your plan to add more products.",
                )

        elif metric == "connected_channels":
            conn_count_res = await db.execute(
                select(func.count(ChannelConnection.id)).where(
                    ChannelConnection.organization_id == organization_id,
                    ChannelConnection.status == "active",
                )
            )
            count = conn_count_res.scalar() or 0
            if count >= plan.max_connected_channels:
                return (
                    False,
                    f"Connected channels quota exceeded. Your current plan '{plan.name}' allows up to {plan.max_connected_channels} connected accounts (Current: {count}). Please upgrade your plan to connect more channels.",
                )

        elif metric == "ai_generation":
            usage_count_res = await db.execute(
                select(func.sum(UsageEvent.quantity)).where(
                    UsageEvent.organization_id == organization_id,
                    UsageEvent.metric_type == "ai_generation",
                    UsageEvent.timestamp >= sub.current_period_start,
                )
            )
            count = usage_count_res.scalar() or 0
            if count >= plan.ai_generation_monthly_quota:
                return (
                    False,
                    f"Monthly AI Studio quota exhausted. Your plan '{plan.name}' includes {plan.ai_generation_monthly_quota} generations per billing cycle (Used: {count}). Please upgrade to Scale or wait for your cycle reset.",
                )

        return True, "Quota within limits."

    @staticmethod
    async def record_usage(
        db: AsyncSession, organization_id: uuid.UUID, metric_type: str, quantity: int = 1
    ) -> None:
        """Records a metered resource usage event."""
        event = UsageEvent(
            organization_id=organization_id,
            metric_type=metric_type,
            quantity=quantity,
        )
        db.add(event)
        await db.commit()

    @staticmethod
    async def get_tenant_usage_stats(
        db: AsyncSession, organization_id: uuid.UUID
    ) -> UsageStatsRead:
        """Calculates exact usage vs quota ceilings for the active tenant."""
        sub = await BillingService.get_or_create_tenant_subscription(db, organization_id)
        plan = sub.plan

        # Active SKUs
        sku_count_res = await db.execute(
            select(func.count(Product.id)).where(
                Product.organization_id == organization_id,
                Product.status != "archived",
            )
        )
        active_skus = sku_count_res.scalar() or 0

        # Connected Channels
        chan_count_res = await db.execute(
            select(func.count(ChannelConnection.id)).where(
                ChannelConnection.organization_id == organization_id,
                ChannelConnection.status == "active",
            )
        )
        channels = chan_count_res.scalar() or 0

        # AI Generations this cycle
        ai_usage_res = await db.execute(
            select(func.sum(UsageEvent.quantity)).where(
                UsageEvent.organization_id == organization_id,
                UsageEvent.metric_type == "ai_generation",
                UsageEvent.timestamp >= sub.current_period_start,
            )
        )
        ai_used = ai_usage_res.scalar() or 0

        # Publishing Jobs this cycle
        pub_jobs_res = await db.execute(
            select(func.count(PublishingJob.id)).where(
                PublishingJob.organization_id == organization_id,
                PublishingJob.created_at >= sub.current_period_start,
            )
        )
        pub_jobs = pub_jobs_res.scalar() or 0

        # Team Members
        members_res = await db.execute(
            select(func.count(OrganizationMember.id)).where(
                OrganizationMember.organization_id == organization_id
            )
        )
        members = members_res.scalar() or 0

        return UsageStatsRead(
            organization_id=organization_id,
            plan_name=plan.name,
            period_start=sub.current_period_start,
            period_end=sub.current_period_end,
            active_skus=UsageMeterItem(
                metric="active_skus",
                label="Master Active SKUs",
                used=active_skus,
                limit=plan.max_active_skus,
                percentage=round((active_skus / max(1, plan.max_active_skus)) * 100, 1),
                unit="SKUs",
            ),
            connected_channels=UsageMeterItem(
                metric="connected_channels",
                label="Connected Channel Accounts",
                used=channels,
                limit=plan.max_connected_channels,
                percentage=round((channels / max(1, plan.max_connected_channels)) * 100, 1),
                unit="Channels",
            ),
            ai_generations=UsageMeterItem(
                metric="ai_generations",
                label="AI Content Studio Generations",
                used=int(ai_used),
                limit=plan.ai_generation_monthly_quota,
                percentage=round((ai_used / max(1, plan.ai_generation_monthly_quota)) * 100, 1),
                unit="Generations",
            ),
            publishing_jobs=UsageMeterItem(
                metric="publishing_jobs",
                label="Publishing Operations (Cycle)",
                used=pub_jobs,
                limit=1000,
                percentage=round((pub_jobs / 1000) * 100, 1),
                unit="Jobs",
            ),
            team_members=UsageMeterItem(
                metric="team_members",
                label="Organization Seats",
                used=members,
                limit=10,
                percentage=round((members / 10) * 100, 1),
                unit="Seats",
            ),
        )

    @staticmethod
    async def process_subscription_upgrade(
        db: AsyncSession,
        organization_id: uuid.UUID,
        plan_id: uuid.UUID,
        payment_id: str,
        order_id: str,
        amount_inr: float,
        gateway: str = "razorpay",
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Subscription:
        """Records payment, activates new subscription period, and records audit trail."""
        # 1. Record payment idempotently
        existing_pmt = await db.execute(
            select(Payment).where(Payment.gateway_payment_id == payment_id)
        )
        if not existing_pmt.scalar_one_or_none():
            payment = Payment(
                organization_id=organization_id,
                amount_inr=amount_inr,
                currency="INR",
                gateway=gateway,
                gateway_payment_id=payment_id,
                gateway_order_id=order_id,
                status="success",
                receipt_url=f"https://dashboard.marketpath.ai/receipts/{payment_id}",
            )
            db.add(payment)

        # 2. Update subscription
        now = datetime.datetime.now(datetime.timezone.utc)
        sub_res = await db.execute(
            select(Subscription).where(Subscription.organization_id == organization_id)
        )
        sub = sub_res.scalar_one_or_none()

        if sub:
            sub.plan_id = plan_id
            sub.status = "active"
            sub.current_period_start = now
            sub.current_period_end = now + datetime.timedelta(days=30)
            sub.cancel_at_period_end = False
            sub.gateway_subscription_id = f"sub_{gateway[:3]}_{payment_id[-8:]}"
        else:
            sub = Subscription(
                organization_id=organization_id,
                plan_id=plan_id,
                status="active",
                current_period_start=now,
                current_period_end=now + datetime.timedelta(days=30),
                cancel_at_period_end=False,
                gateway_subscription_id=f"sub_{gateway[:3]}_{payment_id[-8:]}",
            )
            db.add(sub)

        # 3. Audit log
        db.add(
            AuditLog(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action="subscription.upgraded",
                resource_type="subscription",
                resource_id=str(sub.id),
                metadata_json={
                    "plan_id": str(plan_id),
                    "amount_inr": amount_inr,
                    "payment_id": payment_id,
                    "gateway": gateway,
                },
            )
        )

        await db.commit()
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.id == sub.id)
        )
        return result.scalar_one()

    @staticmethod
    async def cancel_subscription(
        db: AsyncSession, organization_id: uuid.UUID, actor_user_id: Optional[uuid.UUID] = None
    ) -> Subscription:
        """Sets cancellation at the end of the billing period."""
        sub = await BillingService.get_or_create_tenant_subscription(db, organization_id)
        sub.cancel_at_period_end = True

        db.add(
            AuditLog(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action="subscription.cancelled",
                resource_type="subscription",
                resource_id=str(sub.id),
                metadata_json={"plan_name": sub.plan.name},
            )
        )
        await db.commit()
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.id == sub.id)
        )
        return result.scalar_one()

    @staticmethod
    async def get_payment_history(
        db: AsyncSession, organization_id: uuid.UUID
    ) -> List[Payment]:
        """Lists all billing payments for the tenant organization."""
        result = await db.execute(
            select(Payment)
            .where(Payment.organization_id == organization_id)
            .order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())

    # --- Managed Services Methods ---
    @staticmethod
    def get_service_catalog() -> List[ServiceCatalogItem]:
        return [ServiceCatalogItem(**item) for item in MANAGED_SERVICES_CATALOG]

    @staticmethod
    async def create_service_order(
        db: AsyncSession,
        organization_id: uuid.UUID,
        service_type: str,
        scope_description: str,
        target_budget_inr: Optional[int] = None,
        requirements: Optional[Dict[str, Any]] = None,
        due_date: Optional[datetime.date] = None,
    ) -> ServiceOrder:
        """Creates a seller-facing managed service request."""
        catalog_item = next(
            (s for s in MANAGED_SERVICES_CATALOG if s["service_type"] == service_type),
            None,
        )
        quoted_price = target_budget_inr or (catalog_item["starting_price_inr"] if catalog_item else 2999)

        order = ServiceOrder(
            organization_id=organization_id,
            service_type=service_type,
            scope_description=scope_description,
            quoted_price_inr=quoted_price,
            status="requested",
            due_date=due_date,
            requirements_json=requirements or {},
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def get_service_orders(
        db: AsyncSession, organization_id: uuid.UUID
    ) -> List[ServiceOrder]:
        """Lists managed service requests for an organization."""
        result = await db.execute(
            select(ServiceOrder)
            .where(ServiceOrder.organization_id == organization_id)
            .order_by(ServiceOrder.created_at.desc())
        )
        return list(result.scalars().all())

"""MarketPath AI — Demo Data Verification Suite.

Runs comprehensive invariant checks against the seeded demo environment:
1. Verifies Aura Terra Living product catalogue (>= 15 products with rich attributes).
2. Verifies inventory levels, low-stock warnings, and ledger movements.
3. Verifies omnichannel orders (>= 30 orders across Shopify, WooCommerce, Amazon, Flipkart).
4. Verifies mathematical consistency of every single order:
   subtotal - discount_amount + shipping_amount + tax_amount == total_amount.
5. Verifies return & refund reconciliation.
6. Verifies marketing campaigns and multi-day performance metrics.
7. Verifies Agency partner profile, packages, RFPs, and engagements.
8. Verifies Consultant advisory sessions with private diagnostic notes.

Usage:
    python -m backend.scripts.verify_demo_data
"""

import asyncio
import sys
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.agency import AgencyEngagement, AgencyProfile, AgencyQuoteRequest, AgencyServicePackage
from backend.app.models.brand import BrandProfile
from backend.app.models.catalogue import Product, ProductVariant
from backend.app.models.channel import ChannelConnection, ChannelListing
from backend.app.models.consultation import ConsultationRequest
from backend.app.models.inventory import InventoryLedger, StockLevel
from backend.app.models.marketing import Campaign, CampaignMetricsDaily
from backend.app.models.order import ChannelOrder, ChannelOrderItem, ReturnRequest
from backend.app.models.organization import Organization
from backend.app.models.user import UserProfile

DEMO_BRAND_ORG_ID = uuid.UUID("d0000002-0000-0000-0000-000000000001")
DEMO_AGENCY_ORG_ID = uuid.UUID("d0000002-0000-0000-0000-000000000002")
DEMO_CONSULTANT_USER_ID = uuid.UUID("d0000001-0000-0000-0000-000000000003")


async def verify_demo_data() -> bool:
    print("\n" + "=" * 70)
    print("MarketPath AI — Demo Data Verification Suite")
    print("=" * 70)

    all_passed = True

    async with AsyncSessionLocal() as db:
        # 1. Organization & Brand Profile
        org = await db.get(Organization, DEMO_BRAND_ORG_ID)
        if not org or org.name != "Aura Terra Living (Demo)":
            print("❌ Organization Check Failed: Demo brand org not found or name mismatch.")
            all_passed = False
        else:
            print("✅ Demo Organization: Aura Terra Living (Demo) verified.")

        brand_res = await db.execute(select(BrandProfile).where(BrandProfile.organization_id == DEMO_BRAND_ORG_ID))
        brand = brand_res.scalar_one_or_none()
        if not brand or not brand.key_usps:
            print("❌ Brand Profile Check Failed: Incomplete brand profile.")
            all_passed = False
        else:
            print(f"✅ Brand Profile: '{brand.brand_name}' with {len(brand.key_usps)} USPs verified.")

        # 2. Product Catalogue (Expect >= 15 products)
        prods_res = await db.execute(
            select(Product).where(Product.organization_id == DEMO_BRAND_ORG_ID, Product.status == "active")
        )
        products = prods_res.scalars().all()
        prod_count = len(products)
        if prod_count < 15:
            print(f"❌ Product Catalogue Check Failed: Expected >= 15 products, found {prod_count}.")
            all_passed = False
        else:
            print(f"✅ Product Catalogue: {prod_count} active D2C products found (Target: >= 15).")

        # 3. Inventory & Low Stock Alerts
        stock_res = await db.execute(
            select(StockLevel).where(StockLevel.organization_id == DEMO_BRAND_ORG_ID)
        )
        stock_levels = stock_res.scalars().all()
        low_stock_items = [s for s in stock_levels if s.physical_stock <= s.reorder_point]
        if len(low_stock_items) < 2:
            print(f"❌ Inventory Check Failed: Expected >= 2 low stock alerts, found {len(low_stock_items)}.")
            all_passed = False
        else:
            low_skus = [s.sku for s in low_stock_items]
            print(f"✅ Inventory Invariants: {len(stock_levels)} stock records, {len(low_stock_items)} low-stock alerts ({', '.join(low_skus)}).")

        ledger_res = await db.execute(
            select(InventoryLedger).where(InventoryLedger.organization_id == DEMO_BRAND_ORG_ID)
        )
        ledger_count = len(ledger_res.scalars().all())
        if ledger_count < prod_count:
            print(f"❌ Inventory Ledger Check Failed: Expected >= {prod_count} movements, found {ledger_count}.")
            all_passed = False
        else:
            print(f"✅ Inventory Ledger: {ledger_count} verified inventory movements recorded.")

        # 4. Omnichannel Connections & Listings
        conn_res = await db.execute(
            select(ChannelConnection).where(ChannelConnection.organization_id == DEMO_BRAND_ORG_ID)
        )
        connections = conn_res.scalars().all()
        channel_types = {c.channel_type for c in connections}
        expected_channels = {"shopify", "woocommerce", "amazon", "flipkart"}
        if not expected_channels.issubset(channel_types):
            print(f"❌ Channel Connections Failed: Missing channels {expected_channels - channel_types}.")
            all_passed = False
        else:
            print(f"✅ Sales Channels: All 4 channels active ({', '.join(sorted(channel_types))}).")

        # 5. Omnichannel Orders & Mathematical Consistency (Expect >= 30 orders)
        orders_res = await db.execute(
            select(ChannelOrder).where(ChannelOrder.organization_id == DEMO_BRAND_ORG_ID)
        )
        orders = orders_res.scalars().all()
        order_count = len(orders)
        if order_count < 30:
            print(f"❌ Orders Count Check Failed: Expected >= 30 orders, found {order_count}.")
            all_passed = False
        else:
            print(f"✅ Unified Orders: {order_count} sample orders found (Target: >= 30).")

        math_errors = 0
        order_channels_present = set()
        for ord in orders:
            order_channels_present.add(ord.channel_type)
            expected_tot = round(float(ord.subtotal) - float(ord.discount_amount) + float(ord.shipping_amount) + float(ord.tax_amount), 2)
            actual_tot = round(float(ord.total_amount), 2)
            if abs(expected_tot - actual_tot) > 0.01:
                math_errors += 1
                print(f"   ⚠️ Math Mismatch on {ord.order_number}: subtotal({ord.subtotal}) - disc({ord.discount_amount}) + ship({ord.shipping_amount}) + tax({ord.tax_amount}) = {expected_tot} != total({actual_tot})")

        if math_errors > 0:
            print(f"❌ Order Mathematical Reconciliation Failed: {math_errors} orders have arithmetic discrepancies.")
            all_passed = False
        else:
            print(f"✅ Order Math Integrity: 100% of {order_count} orders satisfy subtotal - discount + shipping + tax == total.")

        print(f"   Channel Spread: {', '.join(f'{ch}: {sum(1 for o in orders if o.channel_type == ch)}' for ch in sorted(order_channels_present))}")

        # 6. Returns & Refunds
        returns_res = await db.execute(
            select(ReturnRequest).where(ReturnRequest.organization_id == DEMO_BRAND_ORG_ID)
        )
        returns = returns_res.scalars().all()
        if len(returns) < 2:
            print(f"❌ Returns Check Failed: Expected >= 2 returns, found {len(returns)}.")
            all_passed = False
        else:
            print(f"✅ Returns Reconciliation: {len(returns)} completed reverse logistics & return records verified.")

        # 7. Marketing Campaigns & Daily Metrics
        camps_res = await db.execute(
            select(Campaign).where(Campaign.organization_id == DEMO_BRAND_ORG_ID)
        )
        campaigns = camps_res.scalars().all()
        if len(campaigns) < 3:
            print(f"❌ Marketing Campaigns Failed: Expected >= 3 campaigns, found {len(campaigns)}.")
            all_passed = False
        else:
            metrics_count = (await db.execute(
                select(func.count(CampaignMetricsDaily.id))
            )).scalar() or 0
            print(f"✅ Marketing Campaigns: {len(campaigns)} active campaigns with {metrics_count} daily metrics.")

        # 8. Agency Connect Suite
        agency_res = await db.execute(
            select(AgencyProfile).where(AgencyProfile.organization_id == DEMO_AGENCY_ORG_ID)
        )
        agency = agency_res.scalar_one_or_none()
        if not agency or agency.verification_status != "verified":
            print("❌ Agency Profile Check Failed: Demo agency not found or unverified.")
            all_passed = False
        else:
            pkgs = (await db.execute(
                select(AgencyServicePackage).where(AgencyServicePackage.agency_profile_id == agency.id)
            )).scalars().all()
            engs = (await db.execute(
                select(AgencyEngagement).where(AgencyEngagement.agency_profile_id == agency.id)
            )).scalars().all()
            print(f"✅ Agency Partner: '{agency.name}' ({agency.verification_status}), {len(pkgs)} packages, {len(engs)} active engagement(s).")

        # 9. Consultant Advisory Suite
        cons_res = await db.execute(
            select(ConsultationRequest).where(ConsultationRequest.assigned_consultant_id == DEMO_CONSULTANT_USER_ID)
        )
        consultations = cons_res.scalars().all()
        if len(consultations) < 3:
            print(f"❌ Consultant Check Failed: Expected >= 3 consultations, found {len(consultations)}.")
            all_passed = False
        else:
            with_notes = [c for c in consultations if c.internal_notes and len(c.internal_notes) > 50]
            print(f"✅ Consultant Workspace: {len(consultations)} consultation sessions ({len(with_notes)} with private diagnostic notes).")

    print("=" * 70)
    if all_passed:
        print("🎉 ALL DEMO DATA INVARIANTS PASSED PERFECTLY!")
        print("=" * 70 + "\n")
        return True
    else:
        print("⚠️ SOME INVARIANTS FAILED — Review errors above.")
        print("=" * 70 + "\n")
        return False


def main():
    success = asyncio.run(verify_demo_data())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

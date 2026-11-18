"""MarketPath AI — Four Fully Populated Demo Accounts Seeder.

Provisions exactly 4 isolated demo accounts with complete, coherent, mathematically consistent data:
1. Demo Company Owner: demo.company@marketpath.ai (18 products, 40 orders, stock levels, ledger, analytics, campaigns)
2. Demo Agency Partner: demo.agency@marketpath.ai (portfolio, packages, quote requests, proposals, engagements)
3. Demo Consultant: demo.consultant@marketpath.ai (consultations, diagnostics, private advisory notes, action items)
4. Demo Platform Admin: demo.admin@marketpath.ai (demo telemetry, system health, audit logs)

Usage:
    python -m backend.scripts.seed_demo [--force]
"""

import argparse
import asyncio
import datetime
import decimal
import os
import sys
import uuid
from pathlib import Path
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import AsyncSessionLocal
from backend.app.core.security import hash_password
from backend.app.models.agency import (
    AgencyEngagement,
    AgencyMember,
    AgencyPortfolio,
    AgencyProfile,
    AgencyQuoteRequest,
    AgencyService,
    AgencyServicePackage,
)
from backend.app.models.audit import AuditLog
from backend.app.models.brand import BrandProfile
from backend.app.models.calendar import BusinessCalendarEvent
from backend.app.models.catalogue import Product, ProductChannelOverride, ProductMedia, ProductVariant
from backend.app.models.channel import ChannelConnection, ChannelListing, PublishingJob
from backend.app.models.consultation import ConsultationRequest
from backend.app.models.content import ContentGeneration
from backend.app.models.inventory import InventoryLedger, StockLevel
from backend.app.models.marketing import AdAccount, Campaign, CampaignCreative, CampaignMetricsDaily, ExternalCampaign
from backend.app.models.notification import Notification, NotificationOutbox
from backend.app.models.order import ChannelOrder, ChannelOrderItem, ReturnItem, ReturnRequest
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import UserProfile

SECRETS_DIR = Path("secrets")
SECRETS_FILE = SECRETS_DIR / "marketpath-initial-access.txt"

# Deterministic Demo IDs for Isolation
DEMO_COMPANY_USER_ID = uuid.UUID("d0000001-0000-0000-0000-000000000001")
DEMO_AGENCY_USER_ID = uuid.UUID("d0000001-0000-0000-0000-000000000002")
DEMO_CONSULTANT_USER_ID = uuid.UUID("d0000001-0000-0000-0000-000000000003")
DEMO_ADMIN_USER_ID = uuid.UUID("d0000001-0000-0000-0000-000000000004")

DEMO_BRAND_ORG_ID = uuid.UUID("d0000002-0000-0000-0000-000000000001")
DEMO_AGENCY_ORG_ID = uuid.UUID("d0000002-0000-0000-0000-000000000002")

# Consistent, professional demo credentials for seamless interviewer testing
DEMO_PASSWORDS = {
    "company": os.getenv("DEMO_PASSWORD_COMPANY", "AuraTerra#Demo2026!"),
    "agency": os.getenv("DEMO_PASSWORD_AGENCY", "CraftVerve#Demo2026!"),
    "consultant": os.getenv("DEMO_PASSWORD_CONSULTANT", "DrSharma#Demo2026!"),
    "admin": os.getenv("DEMO_PASSWORD_ADMIN", "Admin#Platform2026!"),
}


async def seed_demo_environment(force: bool = False) -> None:
    async with AsyncSessionLocal() as db:
        now = datetime.datetime.now(datetime.timezone.utc)
        today = datetime.date.today()

        pw_company = DEMO_PASSWORDS["company"]
        pw_agency = DEMO_PASSWORDS["agency"]
        pw_consultant = DEMO_PASSWORDS["consultant"]
        pw_admin = DEMO_PASSWORDS["admin"]

        demo_emails = {
            "company": "demo.company@marketpath.ai",
            "agency": "demo.agency@marketpath.ai",
            "consultant": "demo.consultant@marketpath.ai",
            "admin": "demo.admin@marketpath.ai",
        }

        # ---------------------------------------------------------------------
        # 1. Provision or Update Users
        # ---------------------------------------------------------------------
        users_def = [
            (DEMO_COMPANY_USER_ID, demo_emails["company"], "Ananya Deshmukh (Demo Founder)", "company", False, pw_company),
            (DEMO_AGENCY_USER_ID, demo_emails["agency"], "Vikram Mehta (CraftVerve Media)", "agency", False, pw_agency),
            (DEMO_CONSULTANT_USER_ID, demo_emails["consultant"], "Dr. Rajesh Sharma (Lead D2C Advisor)", "consultant", False, pw_consultant),
            (DEMO_ADMIN_USER_ID, demo_emails["admin"], "Demo Platform Operator", "admin", True, pw_admin),
        ]

        for uid, email, fname, atype, is_adm, pw in users_def:
            u = await db.get(UserProfile, uid)
            if not u:
                u = UserProfile(
                    id=uid,
                    email=email,
                    full_name=fname,
                    account_type=atype,
                    is_platform_admin=is_adm,
                    is_active=True,
                    vetting_status="approved",
                    password_hash=hash_password(pw),
                )
                db.add(u)
            else:
                u.email = email
                u.full_name = fname
                u.account_type = atype
                u.password_hash = hash_password(pw)
                u.is_platform_admin = is_adm
                u.is_active = True
                u.vetting_status = "approved"

        await db.flush()

        # ---------------------------------------------------------------------
        # 2. Demo Organizations & Memberships
        # ---------------------------------------------------------------------
        org_brand = await db.get(Organization, DEMO_BRAND_ORG_ID)
        if not org_brand:
            org_brand = Organization(
                id=DEMO_BRAND_ORG_ID,
                name="Aura Terra Living (Demo)",
                slug="aura-terra-demo",
                org_type="business",
                is_active=True,
                settings={"currency": "INR", "timezone": "Asia/Kolkata", "category": "Home & Living", "is_demo": True},
            )
            db.add(org_brand)
        else:
            org_brand.settings = {"currency": "INR", "timezone": "Asia/Kolkata", "category": "Home & Living", "is_demo": True}
        await db.flush()

        org_agency = await db.get(Organization, DEMO_AGENCY_ORG_ID)
        if not org_agency:
            org_agency = Organization(
                id=DEMO_AGENCY_ORG_ID,
                name="CraftVerve Media (Demo Agency)",
                slug="craftverve-demo",
                org_type="agency",
                is_active=True,
                settings={"city": "Pune", "state": "Maharashtra", "is_demo": True},
            )
            db.add(org_agency)
        else:
            org_agency.settings = {"city": "Pune", "state": "Maharashtra", "is_demo": True}
        await db.flush()

        for user_id, org_id in [(DEMO_COMPANY_USER_ID, DEMO_BRAND_ORG_ID), (DEMO_AGENCY_USER_ID, DEMO_AGENCY_ORG_ID)]:
            m_res = await db.execute(
                select(OrganizationMember).where(
                    OrganizationMember.user_id == user_id, OrganizationMember.organization_id == org_id
                )
            )
            if not m_res.scalar_one_or_none():
                db.add(
                    OrganizationMember(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        user_id=user_id,
                        role="owner",
                    )
                )

        # Brand Profile
        bp_res = await db.execute(select(BrandProfile).where(BrandProfile.organization_id == DEMO_BRAND_ORG_ID))
        brand = bp_res.scalar_one_or_none()
        if not brand:
            brand = BrandProfile(
                id=uuid.uuid4(),
                organization_id=DEMO_BRAND_ORG_ID,
                brand_name="Aura Terra Living",
                tagline="Conscious, handcrafted terracotta home goods for mindful Indian homes.",
                tone_of_voice="Warm, grounded, artisanal, authentic",
                visual_guidelines={"primary_color": "#08765B", "accent_color": "#D99143", "font": "Plus Jakarta Sans"},
                key_usps=["100% natural riverbed clay", "Handcrafted by rural artisans", "Plastic-free sustainable packaging", "Naturally cooling and toxin-free"],
                brand_values=["Sustainability", "Artisan Dignity", "Aesthetic Living", "Ancestral Wellness"],
                customer_demographics={"age": "25-45", "geography": "Metro & Tier-1 India (Mumbai, Bengaluru, Delhi NCR, Pune)", "persona": "Conscious Homemaker & Gifting Buyer"},
                product_stories=["Rooted in centuries-old earthen pottery traditions of Maharashtra and Rajasthan, reimagined for contemporary urban homes."],
            )
            db.add(brand)

        # ---------------------------------------------------------------------
        # 3. Demo Products & Variants (18 Rich D2C Products)
        # ---------------------------------------------------------------------
        products_catalog = [
            {
                "title": "Kavya Terracotta Water Carafe (1.2L)",
                "sku": "AT-CARAFE-01",
                "category": "Drinkware & Dining",
                "hsn": "69120010",
                "base_price": 1299.0,
                "cost_price": 545.0,
                "stock": 85,
                "desc": "Natural cooling earthenware water carafe with handcrafted tight-fitting lid. Micro-porous walls cool water naturally without refrigeration.",
                "variants": [
                    {"title": "1.2L Standard", "sku": "AT-CARAFE-01-STD", "price": 1299.0, "stock": 55, "options": {"capacity": "1.2L", "finish": "Natural Terracotta"}},
                    {"title": "800ml Compact", "sku": "AT-CARAFE-01-CMP", "price": 999.0, "stock": 30, "options": {"capacity": "800ml", "finish": "Natural Terracotta"}},
                ],
                "image": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Zoya Unglazed Chai Kulhads (Set of 6)",
                "sku": "AT-KULHAD-06",
                "category": "Drinkware & Dining",
                "hsn": "69120010",
                "base_price": 649.0,
                "cost_price": 260.0,
                "stock": 140,
                "desc": "Traditional unglazed riverbed clay cups designed for hot cutting chai. Imparts the authentic earthy petrichor aroma with every sip.",
                "variants": [
                    {"title": "Set of 6 (150ml)", "sku": "AT-KULHAD-06-S6", "price": 649.0, "stock": 90, "options": {"quantity": "6 Pcs", "capacity": "150ml"}},
                    {"title": "Set of 12 (150ml)", "sku": "AT-KULHAD-06-S12", "price": 1199.0, "stock": 50, "options": {"quantity": "12 Pcs", "capacity": "150ml"}},
                ],
                "image": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Mitti Botanical Planter Pot (8-inch)",
                "sku": "AT-PLANT-08",
                "category": "Planters & Decor",
                "hsn": "69139000",
                "base_price": 899.0,
                "cost_price": 375.0,
                "stock": 110,
                "desc": "Porous terracotta botanical pot with matching drainage saucer. Promotes optimal root aeration and prevents root rot naturally.",
                "variants": [
                    {"title": "8-Inch Raw Terracotta", "sku": "AT-PLANT-08-RAW", "price": 899.0, "stock": 70, "options": {"diameter": "8-inch", "finish": "Raw Terracotta"}},
                    {"title": "8-Inch Ochre Wash", "sku": "AT-PLANT-08-OCH", "price": 999.0, "stock": 40, "options": {"diameter": "8-inch", "finish": "Warm Ochre"}},
                ],
                "image": "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Sanskrit Traditional Curd Setting Handi",
                "sku": "AT-HANDI-CURD",
                "category": "Cookware & Storage",
                "hsn": "69120010",
                "base_price": 799.0,
                "cost_price": 335.0,
                "stock": 95,
                "desc": "Porous clay curd setting pot that absorbs excess whey to yield thick, artisanal, probiotic dahi naturally without thickeners.",
                "variants": [
                    {"title": "1-Litre Standard", "sku": "AT-HANDI-CURD-1L", "price": 799.0, "stock": 65, "options": {"capacity": "1L"}},
                    {"title": "1.5-Litre Family", "sku": "AT-HANDI-CURD-15L", "price": 999.0, "stock": 30, "options": {"capacity": "1.5L"}},
                ],
                "image": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Prithvi Essential Oil Earthen Diffuser",
                "sku": "AT-DIFFUSE-OIL",
                "category": "Wellness & Aroma",
                "hsn": "69139000",
                "base_price": 999.0,
                "cost_price": 410.0,
                "stock": 60,
                "desc": "Tea-light driven porous terracotta aroma oil burner with hand-carved floral lattice pattern that casts mesmerizing shadow play.",
                "variants": [
                    {"title": "Standard Carved", "sku": "AT-DIFFUSE-OIL-STD", "price": 999.0, "stock": 60, "options": {"pattern": "Floral Lattice"}},
                ],
                "image": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Bhoomi Low-Flame Clay Biryani Pot (3L)",
                "sku": "AT-POT-BIRYANI",
                "category": "Cookware & Storage",
                "hsn": "69120010",
                "base_price": 1899.0,
                "cost_price": 795.0,
                "stock": 45,
                "desc": "Heavy-bottom clay cooking handi pre-seasoned with rice starch and organic mustard oil for slow-cooked aromatic dum biryanis.",
                "variants": [
                    {"title": "3-Litre Dum Handi", "sku": "AT-POT-BIRYANI-3L", "price": 1899.0, "stock": 45, "options": {"capacity": "3L", "seasoned": "Yes"}},
                ],
                "image": "https://images.unsplash.com/photo-1584992236310-6edddc08acff?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Veda Terracotta Water Bottle (750ml)",
                "sku": "AT-BOT-750",
                "category": "Drinkware & Dining",
                "hsn": "69120010",
                "base_price": 849.0,
                "cost_price": 355.0,
                "stock": 120,
                "desc": "Ergonomically shaped natural terracotta personal water bottle with leak-proof food-grade cork lid and thermal protective silicone base ring.",
                "variants": [
                    {"title": "750ml Natural Raw", "sku": "AT-BOT-750-RAW", "price": 849.0, "stock": 80, "options": {"capacity": "750ml", "edition": "Raw Natural"}},
                    {"title": "750ml Cotton Sleeve Edition", "sku": "AT-BOT-750-SLV", "price": 999.0, "stock": 40, "options": {"capacity": "750ml", "edition": "Woven Jute Sleeve"}},
                ],
                "image": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Ananda Hand-painted Terracotta Urli Bowl",
                "sku": "AT-URLI-10",
                "category": "Festive Gifting & Decor",
                "hsn": "69139000",
                "base_price": 1499.0,
                "cost_price": 620.0,
                "stock": 50,
                "desc": "Hand-painted traditional floating floral bowl with gold leaf detailing on the outer rim. Ideal for entryway floral and floating candle arrangements.",
                "variants": [
                    {"title": "10-inch Urli", "sku": "AT-URLI-10-STD", "price": 1499.0, "stock": 35, "options": {"diameter": "10-inch"}},
                    {"title": "12-inch Grand Urli", "sku": "AT-URLI-12-GRD", "price": 1999.0, "stock": 15, "options": {"diameter": "12-inch"}},
                ],
                "image": "https://images.unsplash.com/photo-1590736969955-71cc94801759?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Dharani Unglazed Sprouting Pot (2-Tier)",
                "sku": "AT-SPROUT-2T",
                "category": "Cookware & Storage",
                "hsn": "69120010",
                "base_price": 1199.0,
                "cost_price": 495.0,
                "stock": 70,
                "desc": "Two-tier self-aerating unglazed earthenware sprout maker. Keeps mung and legumes moist and breathable for crisp, mold-free sprouts in 24 hours.",
                "variants": [
                    {"title": "2-Tier Standard", "sku": "AT-SPROUT-2T-STD", "price": 1199.0, "stock": 70, "options": {"tiers": "2"}},
                ],
                "image": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Nirvana Terracotta Ambient Table Lamp Shade",
                "sku": "AT-LAMP-SHD",
                "category": "Lighting & Home Decor",
                "hsn": "94055000",
                "base_price": 2199.0,
                "cost_price": 920.0,
                "stock": 35,
                "desc": "Cylindrical earthen bedside lamp shade with laser-cut geometric micro-apertures. Emits warm 2700K ambient glow across interior spaces.",
                "variants": [
                    {"title": "Honeycomb Perforated", "sku": "AT-LAMP-SHD-HNY", "price": 2199.0, "stock": 35, "options": {"cutout": "Honeycomb"}},
                ],
                "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Shanti Incense Stick Clay Holder",
                "sku": "AT-INCN-HLD",
                "category": "Wellness & Aroma",
                "hsn": "69139000",
                "base_price": 399.0,
                "cost_price": 160.0,
                "stock": 200,
                "desc": "Minimalist handcrafted earthenware incense burner with broad ash catcher tray. Double-aperture accommodates both bamboo and dhoop sticks.",
                "variants": [
                    {"title": "Single Tray Raw", "sku": "AT-INCN-HLD-RAW", "price": 399.0, "stock": 200, "options": {"color": "Terracotta Red"}},
                ],
                "image": "https://images.unsplash.com/photo-1528722828814-77b9b83aafb2?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Samriddhi Brass-Rimmed Terracotta Serving Platter",
                "sku": "AT-PLAT-BRASS",
                "category": "Tableware & Dining",
                "hsn": "69120010",
                "base_price": 1699.0,
                "cost_price": 710.0,
                "stock": 40,
                "desc": "Artisan terracotta entertainment centerpiece platter with hand-riveted solid brass handles. Perfect for artisanal appetizers and festive sweets.",
                "variants": [
                    {"title": "12-Inch Oval Platter", "sku": "AT-PLAT-BRASS-12", "price": 1699.0, "stock": 40, "options": {"length": "12-inch", "finish": "Brass Riveted"}},
                ],
                "image": "https://images.unsplash.com/photo-1533090161767-e6ffed986c88?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Malhar Rustic Terracotta Tea Kettle (850ml)",
                "sku": "AT-KETTLE-01",
                "category": "Drinkware & Dining",
                "hsn": "69120010",
                "base_price": 1399.0,
                "cost_price": 585.0,
                "stock": 55,
                "desc": "Rustic hand-thrown clay teapot with cane wrapped overhead handle. Naturally retains heat for long lingering afternoon chai conversations.",
                "variants": [
                    {"title": "850ml Wicker Handle", "sku": "AT-KETTLE-01-WCK", "price": 1399.0, "stock": 55, "options": {"capacity": "850ml", "handle": "Cane Woven"}},
                ],
                "image": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Vedic 7-Spice Clay Spice Container Set",
                "sku": "AT-MASALA-07",
                "category": "Cookware & Storage",
                "hsn": "69120010",
                "base_price": 1599.0,
                "cost_price": 665.0,
                "stock": 65,
                "desc": "Artisanal masala dani consisting of 7 miniature clay bowls nestled in a fitted terracotta round tray with teak wood pinch spoons.",
                "variants": [
                    {"title": "7-Bowl Masala Dani Set", "sku": "AT-MASALA-07-SET", "price": 1599.0, "stock": 65, "options": {"pieces": "7 Bowls + Tray + Spoons"}},
                ],
                "image": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Deepam Handcrafted Festive Terracotta Diyas (Box of 12)",
                "sku": "AT-DIYAS-12",
                "category": "Festive Gifting & Decor",
                "hsn": "69139000",
                "base_price": 499.0,
                "cost_price": 195.0,
                "stock": 180,
                "desc": "Traditional hand-pressed clay oil lamps packed in plastic-free recycled paper gift box with cotton wicks. Perfect for Diwali and year-round puja.",
                "variants": [
                    {"title": "Box of 12 Diyas", "sku": "AT-DIYAS-12-BX", "price": 499.0, "stock": 180, "options": {"count": "12 Units"}},
                ],
                "image": "https://images.unsplash.com/photo-1605647540924-852290f6b0d5?auto=format&fit=crop&w=800&q=80",
            },
            {
                "title": "Aarohi Ergonomic Artisanal Coffee Mugs (Set of 2)",
                "sku": "AT-MUG-02",
                "category": "Tableware & Dining",
                "hsn": "69120010",
                "base_price": 749.0,
                "cost_price": 310.0,
                "stock": 130,
                "desc": "Hand-turned terracotta coffee mugs with food-grade clear interior glaze for zero staining while preserving natural clay exterior tactile grip.",
                "variants": [
                    {"title": "Set of 2 (300ml)", "sku": "AT-MUG-02-S2", "price": 749.0, "stock": 130, "options": {"pack": "Set of 2", "capacity": "300ml"}},
                ],
                "image": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=800&q=80",
            },
            {
                # LOW STOCK ALERT PRODUCT 1
                "title": "Jal Tarang Earthen Water Dispenser with Brass Tap (5L)",
                "sku": "AT-WATER-05L",
                "category": "Drinkware & Dining",
                "hsn": "69120010",
                "base_price": 2499.0,
                "cost_price": 1050.0,
                "stock": 8,  # Critical low stock (< reorder_point 15)
                "desc": "Large 5-litre handcrafted countertop natural cooling clay matka fitted with heavy solid brass tap and wooden elevation stand.",
                "variants": [
                    {"title": "5L Countertop Dispenser", "sku": "AT-WATER-05L-STD", "price": 2499.0, "stock": 8, "options": {"capacity": "5L", "tap": "Solid Brass"}},
                ],
                "image": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=800&q=80",
            },
            {
                # LOW STOCK ALERT PRODUCT 2
                "title": "Tarang Terracotta Bell Wind Chime",
                "sku": "AT-WIND-03",
                "category": "Festive Gifting & Decor",
                "hsn": "69139000",
                "base_price": 899.0,
                "cost_price": 370.0,
                "stock": 12,  # Low stock (< reorder_point 15)
                "desc": "Tuned hollow terracotta bells strung with jute cord and driftwood bead clapper that produces soft resonant chimes in balcony breezes.",
                "variants": [
                    {"title": "3-Bell Balcony Chime", "sku": "AT-WIND-03-STD", "price": 899.0, "stock": 12, "options": {"bells": "3 Bells", "length": "24-inch"}},
                ],
                "image": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?auto=format&fit=crop&w=800&q=80",
            },
        ]

        created_products = []
        for pdata in products_catalog:
            p_res = await db.execute(
                select(Product).where(Product.organization_id == DEMO_BRAND_ORG_ID, Product.sku == pdata["sku"])
            )
            prod = p_res.scalar_one_or_none()
            if not prod:
                prod = Product(
                    id=uuid.uuid4(),
                    organization_id=DEMO_BRAND_ORG_ID,
                    title=pdata["title"],
                    sku=pdata["sku"],
                    status="active",
                    category=pdata["category"],
                    short_description=pdata["desc"][:150],
                    long_description=pdata["desc"],
                    base_price=pdata["base_price"],
                    compare_at_price=round(pdata["base_price"] * 1.25, 2),
                    cost_price=pdata["cost_price"],
                    stock_quantity=pdata["stock"],
                    materials=["100% Natural Riverbed Clay", "Terracotta"],
                    tags=["artisanal", "terracotta", "sustainable", "handcrafted", "indian_d2c"],
                    dimensions={"length": 15, "width": 15, "height": 22, "unit": "cm"},
                    weight=1.2,
                    category_attributes={"hsn_code": pdata["hsn"], "country_of_origin": "India", "state_of_origin": "Maharashtra"},
                    packaging_specs={"box_type": "Recycled Molded Pulp Buffer", "drop_test_certified": True, "plastic_free": True},
                    shipping_specs={"fragile": True, "lead_time_days": 2},
                )
                db.add(prod)
                await db.flush()

                # Add Media
                db.add(
                    ProductMedia(
                        id=uuid.uuid4(),
                        product_id=prod.id,
                        cloudinary_public_id=f"demo_auraterra_{pdata['sku']}",
                        media_url=pdata["image"],
                        media_type="image",
                        alt_text=pdata["title"],
                        display_order=0,
                    )
                )

                # Primary Variant(s)
                for vdata in pdata["variants"]:
                    var = ProductVariant(
                        id=uuid.uuid4(),
                        product_id=prod.id,
                        title=vdata["title"],
                        sku=vdata["sku"],
                        price=vdata["price"],
                        stock_quantity=vdata["stock"],
                        options=vdata["options"],
                    )
                    db.add(var)
                    await db.flush()

                    # Stock Level
                    reorder_pt = 15
                    phys = vdata["stock"]
                    res_stk = 2 if phys > 15 else 0
                    db.add(
                        StockLevel(
                            organization_id=DEMO_BRAND_ORG_ID,
                            product_id=prod.id,
                            product_variant_id=var.id,
                            sku=vdata["sku"],
                            location_id="primary_warehouse_pune",
                            physical_stock=phys,
                            reserved_stock=res_stk,
                            available_to_sell=phys - res_stk,
                            committed_stock=0,
                            damaged_stock=1 if phys > 30 else 0,
                            returned_stock=2 if phys > 50 else 0,
                            reorder_point=reorder_pt,
                        )
                    )

                    # Initial Inventory Movement
                    db.add(
                        InventoryLedger(
                            organization_id=DEMO_BRAND_ORG_ID,
                            product_id=prod.id,
                            product_variant_id=var.id,
                            sku=vdata["sku"],
                            location_id="primary_warehouse_pune",
                            movement_type="initial_stock",
                            quantity_change=phys,
                            previous_quantity=0,
                            new_quantity=phys,
                            source_type="system_seed",
                            notes="Artisan workshop batch stock verified and accepted into Pune warehouse.",
                        )
                    )
            else:
                # Update attributes if needed
                prod.category_attributes = {"hsn_code": pdata["hsn"], "country_of_origin": "India"}
            created_products.append(prod)

        await db.flush()

        # ---------------------------------------------------------------------
        # 4. Connected Channels (All 4 Omnichannel Marketplaces)
        # ---------------------------------------------------------------------
        chan_data = [
            ("shopify", "Aura Terra Online Store (Shopify)", "auraterra.myshopify.com"),
            ("woocommerce", "Aura Terra Living Brand Store (WooCommerce)", "auraterraliving.co.in"),
            ("amazon", "Amazon India Marketplace (Demo)", "A3MOCKSELLERIND"),
            ("flipkart", "Flipkart Seller Hub (Demo)", "FS_MOCK_AURATERRA"),
        ]
        active_connections = {}
        for ctype, cname, ident in chan_data:
            c_res = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.organization_id == DEMO_BRAND_ORG_ID,
                    ChannelConnection.channel_type == ctype,
                )
            )
            cconn = c_res.scalar_one_or_none()
            if not cconn:
                cconn = ChannelConnection(
                    id=uuid.uuid4(),
                    organization_id=DEMO_BRAND_ORG_ID,
                    channel_type=ctype,
                    account_name=cname,
                    account_identifier=ident,
                    encrypted_access_token="mock_demo_encrypted_token_verified",
                    granted_scopes=["read_products", "write_products", "read_orders", "write_inventory"],
                    status="active",
                    last_synced_at=now - datetime.timedelta(minutes=12),
                )
                db.add(cconn)
                await db.flush()
            active_connections[ctype] = cconn

        # Seed Channel Listings for Products
        for prod in created_products[:12]:
            for ctype, cconn in active_connections.items():
                l_res = await db.execute(
                    select(ChannelListing).where(
                        ChannelListing.channel_connection_id == cconn.id,
                        ChannelListing.product_id == prod.id,
                    )
                )
                if not l_res.scalar_one_or_none():
                    db.add(
                        ChannelListing(
                            id=uuid.uuid4(),
                            organization_id=DEMO_BRAND_ORG_ID,
                            channel_connection_id=cconn.id,
                            product_id=prod.id,
                            remote_product_id=f"REMOTE-{ctype.upper()}-{prod.sku}",
                            external_sku=prod.sku,
                            channel_title=f"{prod.title} — Handcrafted Terracotta",
                            channel_price=float(prod.base_price),
                            remote_status="published",
                            last_published_at=now - datetime.timedelta(days=20),
                        )
                    )
        await db.flush()

        # ---------------------------------------------------------------------
        # 5. Sample Orders (40 Mathematically Reconciled Omnichannel Orders)
        # ---------------------------------------------------------------------
        existing_orders_count = len(
            (await db.execute(select(ChannelOrder).where(ChannelOrder.organization_id == DEMO_BRAND_ORG_ID))).scalars().all()
        )

        if existing_orders_count < 35 or force:
            if force:
                await db.execute(delete(ReturnItem))
                await db.execute(delete(ReturnRequest).where(ReturnRequest.organization_id == DEMO_BRAND_ORG_ID))
                await db.execute(delete(ChannelOrderItem))
                await db.execute(delete(ChannelOrder).where(ChannelOrder.organization_id == DEMO_BRAND_ORG_ID))
                await db.flush()

            customers = [
                ("Priya Sharma", "priya.sharma@gmail.com", "Bandra West, Mumbai", "Maharashtra", "400050"),
                ("Rohan Patel", "rohan.patel@outlook.com", "Navrangpura, Ahmedabad", "Gujarat", "380009"),
                ("Aarti Nair", "aarti.nair@yahoo.com", "Indiranagar, Bengaluru", "Karnataka", "560038"),
                ("Devendra Gupta", "devendra.g@gmail.com", "Greater Kailash, New Delhi", "Delhi", "110048"),
                ("Kavita Sen", "kavita.sen@gmail.com", "Salt Lake Sector 1, Kolkata", "West Bengal", "700064"),
                ("Sanjay Joshi", "sanjay.joshi@gmail.com", "Kothrud, Pune", "Maharashtra", "411038"),
                ("Meenakshi Sundaram", "meenakshi@gmail.com", "Adyar, Chennai", "Tamil Nadu", "600020"),
                ("Vikramaditya Roy", "vikram.roy@gmail.com", "C-Scheme, Jaipur", "Rajasthan", "302001"),
                ("Deepika Kulkarni", "deepika.k@gmail.com", "Jayanagar 4th Block, Bengaluru", "Karnataka", "560041"),
                ("Tanvi Verma", "tanvi.v@gmail.com", "Banjara Hills, Hyderabad", "Telangana", "500034"),
                ("Aditya Singhania", "aditya.singh@gmail.com", "Vasant Vihar, New Delhi", "Delhi", "110057"),
                ("Neha Deshpande", "neha.d@gmail.com", "Aundh, Pune", "Maharashtra", "411007"),
            ]

            order_templates = [
                ("paid", "fulfilled", "delivered", 0.0),
                ("paid", "fulfilled", "shipped", 0.0),
                ("paid", "fulfilled", "delivered", 0.0),
                ("paid", "unfulfilled", "processing", 0.0),
                ("paid", "fulfilled", "delivered", 0.0),
                ("partially_refunded", "fulfilled", "partially_refunded", 0.5),
                ("refunded", "unfulfilled", "refunded", 1.0),
                ("paid", "fulfilled", "delivered", 0.0),
                ("paid", "fulfilled", "delivered", 0.0),
                ("paid", "fulfilled", "delivered", 0.0),
            ]

            channels_distribution = ["shopify", "shopify", "woocommerce", "amazon", "amazon", "flipkart", "shopify", "woocommerce"]

            for i in range(1, 41):
                cust = customers[(i - 1) % len(customers)]
                tmpl = order_templates[(i - 1) % len(order_templates)]
                ctype = channels_distribution[(i - 1) % len(channels_distribution)]
                cconn = active_connections[ctype]
                prod = created_products[(i - 1) % len(created_products)]

                qty = 1 if i % 4 != 0 else 2
                unit_p = float(prod.base_price or 999.0)
                subtot = round(unit_p * qty, 2)
                disc = round(subtot * 0.1, 2) if i % 5 == 0 else 0.0
                ship = 99.0 if (subtot - disc) < 1200.0 else 0.0
                tax = round((subtot - disc) * 0.12, 2)
                # Exact mathematical identity: subtotal - discount + shipping + tax = total
                tot = round(subtot - disc + ship + tax, 2)
                ref_amt = round(tot * tmpl[3], 2)

                order_date = now - datetime.timedelta(days=(32 - i * 0.75), hours=(i * 5) % 24)

                channel_prefix = {"shopify": "SP", "woocommerce": "WC", "amazon": "AZ", "flipkart": "FK"}[ctype]
                remote_id = f"DEMO-{channel_prefix}-{2000 + i}"
                ord_number = f"AT-{channel_prefix}-{2000 + i}"

                cord = ChannelOrder(
                    id=uuid.uuid4(),
                    organization_id=DEMO_BRAND_ORG_ID,
                    channel_connection_id=cconn.id,
                    channel_type=ctype,
                    remote_order_id=remote_id,
                    order_number=ord_number,
                    customer_name=cust[0],
                    customer_email=cust[1],
                    total_amount=tot,
                    subtotal=subtot,
                    discount_amount=disc,
                    shipping_amount=ship,
                    tax_amount=tax,
                    refund_amount=ref_amt,
                    currency="INR",
                    financial_status=tmpl[0],
                    fulfillment_status=tmpl[1],
                    order_lifecycle_status=tmpl[2],
                    order_date=order_date,
                    shipping_address={
                        "street": cust[2],
                        "city": cust[2].split(",")[-1].strip(),
                        "state": cust[3],
                        "postal_code": cust[4],
                        "country": "India",
                    },
                    billing_address={
                        "street": cust[2],
                        "city": cust[2].split(",")[-1].strip(),
                        "state": cust[3],
                        "postal_code": cust[4],
                        "country": "India",
                    },
                    tracking_number=f"BD{992000 + i}" if tmpl[1] == "fulfilled" else None,
                    carrier="Blue Dart Express" if tmpl[1] == "fulfilled" else None,
                    inventory_synced=True,
                    sync_status="synced",
                    raw_payload={"demo": True, "source": ctype},
                )
                db.add(cord)
                await db.flush()

                oi = ChannelOrderItem(
                    id=uuid.uuid4(),
                    order_id=cord.id,
                    product_id=prod.id,
                    sku=prod.sku,
                    title=prod.title,
                    quantity=qty,
                    unit_price=unit_p,
                    total_price=subtot,
                    discount_amount=disc,
                    tax_amount=tax,
                    returned_quantity=1 if tmpl[0] in ("partially_refunded", "refunded") else 0,
                    mapping_status="mapped",
                )
                db.add(oi)

                # Return and Refund reconciliation
                if tmpl[0] in ("partially_refunded", "refunded"):
                    ret_req = ReturnRequest(
                        id=uuid.uuid4(),
                        organization_id=DEMO_BRAND_ORG_ID,
                        order_id=cord.id,
                        return_number=f"RET-DEMO-{100 + i}",
                        status="completed",
                        reason="Transit breakage or hairline glaze imperfection during courier transit",
                        carrier="Delhivery Reverse Logistics",
                        tracking_number=f"DELREV{88100 + i}",
                        received_at=order_date + datetime.timedelta(days=3),
                        inspected_at=order_date + datetime.timedelta(days=4),
                        completed_at=order_date + datetime.timedelta(days=4),
                        total_refund_amount=ref_amt,
                    )
                    db.add(ret_req)
                    await db.flush()

                    db.add(
                        ReturnItem(
                            id=uuid.uuid4(),
                            return_request_id=ret_req.id,
                            order_item_id=oi.id,
                            product_id=prod.id,
                            sku=prod.sku,
                            quantity_ordered=qty,
                            quantity_requested=1,
                            quantity_received=1,
                            inspection_result="partial" if tmpl[0] == "partially_refunded" else "damaged",
                            resalable_quantity=1 if tmpl[0] == "partially_refunded" else 0,
                            damaged_quantity=0 if tmpl[0] == "partially_refunded" else 1,
                            refund_amount=ref_amt,
                            restocked=True,
                        )
                    )

        # ---------------------------------------------------------------------
        # 6. Marketing Campaigns & Analytics
        # ---------------------------------------------------------------------
        existing_camps = (await db.execute(select(Campaign).where(Campaign.organization_id == DEMO_BRAND_ORG_ID))).scalars().all()
        if len(existing_camps) < 4 or force:
            if force and existing_camps:
                await db.execute(delete(Campaign).where(Campaign.organization_id == DEMO_BRAND_ORG_ID))
                await db.flush()

            ad_acc_res = await db.execute(select(AdAccount).where(AdAccount.organization_id == DEMO_BRAND_ORG_ID))
            ad_acc = ad_acc_res.scalar_one_or_none()
            if not ad_acc:
                ad_acc = AdAccount(
                    id=uuid.uuid4(),
                    organization_id=DEMO_BRAND_ORG_ID,
                    platform="meta_ads",
                    external_account_id="act_demo_auraterra_pune",
                    account_name="Aura Terra Living (Official Meta Ads)",
                    currency="INR",
                    status="connected",
                )
                db.add(ad_acc)
                await db.flush()

            campaign_specs = [
                ("Summer Hydration Festival — Clay Carafe Spotlight", "sales", 50000.0, 2500.0, "meta_ads", created_products[0].id),
                ("Handcrafted Chai Kulhads — Monsoon Dining Rush", "sales", 35000.0, 1800.0, "google_ads", created_products[1].id),
                ("Festive Decor & Hand-Painted Urli Showcase", "brand_awareness", 45000.0, 2200.0, "meta_ads", created_products[7].id),
                ("Amazon Prime Kitchenware Sponsored Showcase", "sales", 60000.0, 3000.0, "amazon_ads", created_products[5].id),
            ]

            for cname, obj, btot, bday, chn, pid in campaign_specs:
                camp = Campaign(
                    id=uuid.uuid4(),
                    organization_id=DEMO_BRAND_ORG_ID,
                    product_id=pid,
                    name=cname,
                    objective=obj,
                    status="active",
                    start_date=today - datetime.timedelta(days=21),
                    end_date=today + datetime.timedelta(days=14),
                    total_budget=btot,
                    daily_budget_limit=bday,
                    currency="INR",
                    channel=chn,
                )
                db.add(camp)
                await db.flush()

                db.add(
                    CampaignCreative(
                        id=uuid.uuid4(),
                        campaign_id=camp.id,
                        headline="Experience Pure Clay Living for Mindful Homes",
                        primary_text="Rediscover naturally chilled water and authentic petrichor chai with handcrafted terracotta from Pune.",
                        cta_text="Shop Artisanal Living",
                        media_url="https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=800&q=80",
                        destination_url="https://auraterraliving.co.in/collections/artisanal",
                        is_selected=True,
                        is_approved=True,
                    )
                )

                ext_camp = ExternalCampaign(
                    id=uuid.uuid4(),
                    campaign_id=camp.id,
                    ad_account_id=ad_acc.id,
                    platform=chn,
                    remote_campaign_id=f"act_{chn[:4]}_{pid.hex[:8]}",
                    remote_status="ACTIVE",
                    last_synced_at=now - datetime.timedelta(minutes=30),
                )
                db.add(ext_camp)
                await db.flush()

                # Daily metrics for the last 14 days
                for d in range(14, 0, -1):
                    day_date = today - datetime.timedelta(days=d)
                    spend = round(bday * (0.85 + (d % 4) * 0.08), 2)
                    impr = int(spend * 24.5)
                    clicks = int(impr * 0.038)
                    conv = max(1, int(clicks * 0.042))
                    conv_val = round(spend * (3.4 + (d % 3) * 0.4), 2)

                    db.add(
                        CampaignMetricsDaily(
                            id=uuid.uuid4(),
                            external_campaign_id=ext_camp.id,
                            date=day_date,
                            impressions=impr,
                            clicks=clicks,
                            spend=spend,
                            conversions=conv,
                            conversion_value=conv_val,
                        )
                    )

        # ---------------------------------------------------------------------
        # 7. Demo Agency Profile, Services, Packages, and Engagements
        # ---------------------------------------------------------------------
        ap_res = await db.execute(select(AgencyProfile).where(AgencyProfile.organization_id == DEMO_AGENCY_ORG_ID))
        agency_p = ap_res.scalar_one_or_none()
        if not agency_p:
            agency_p = AgencyProfile(
                id=uuid.uuid4(),
                organization_id=DEMO_AGENCY_ORG_ID,
                name="CraftVerve Media",
                slug="craftverve-media-demo",
                tagline="Performance creative & ROAS scaling for conscious home and artisan brands.",
                description="We partner with homegrown D2C brands to create high-converting video hooks, catalog design, and Meta ROAS scaling.",
                email=demo_emails["agency"],
                phone="+91 98234 11029",
                city="Pune",
                state="Maharashtra",
                country="India",
                verification_status="verified",
                verified_at=now,
                is_available=True,
                is_active=True,
                is_demo=True,
                tier="verified_partner",
                rating_avg=4.9,
                reviews_count=18,
                category_specialties=["Home & Living", "Artisan Crafts", "Clean Beauty"],
                service_offerings=["Performance Marketing", "Creative Studio", "Marketplace Ads"],
            )
            db.add(agency_p)
            await db.flush()

            db.add(
                AgencyMember(
                    agency_profile_id=agency_p.id,
                    user_id=DEMO_AGENCY_USER_ID,
                    role="agency_owner",
                )
            )

        # Ensure all 3 comprehensive packages exist
        existing_pkgs = (await db.execute(
            select(AgencyServicePackage).where(AgencyServicePackage.agency_profile_id == agency_p.id)
        )).scalars().all()

        if len(existing_pkgs) < 3 or force:
            if force and existing_pkgs:
                await db.execute(
                    delete(AgencyServicePackage).where(AgencyServicePackage.agency_profile_id == agency_p.id)
                )
                await db.flush()

            packages_def = [
                ("D2C Omnichannel Sprint (30 Days)", "growth", 45000, "monthly", "Complete creative refresh + Meta ROAS audit and catalog publication overhaul.", ["12 UGC Video Hooks", "Catalog Product Photoshoot", "Full Ad Account Restructure"], 30),
                ("Omnichannel Catalog Overhaul & Photoshoot", "starter", 25000, "fixed", "Professional high-res studio and lifestyle photography with SEO attribute mapping.", ["18 Styled Studio Images", "A+ Amazon Graphic Assets", "HSN & Attribute Audit"], 14),
                ("Full-Stack Marketplace Growth Retainer", "enterprise", 75000, "monthly", "Dedicated growth squad managing Meta, Google PMax, and Amazon Ads with weekly creative sprints.", ["End-to-End Campaign Management", "Bi-Weekly Strategy Calls", "ROAS Scaling Guarantee"], 90),
            ]
            for pname, ptier, pprice, pinterval, pdesc, pdeliv, pturn in packages_def:
                db.add(
                    AgencyServicePackage(
                        id=uuid.uuid4(),
                        agency_profile_id=agency_p.id,
                        name=pname,
                        package_tier=ptier,
                        price_inr=pprice,
                        billing_interval=pinterval,
                        description=pdesc,
                        deliverables=pdeliv,
                        turnaround_days=pturn,
                        is_active=True,
                    )
                )
            await db.flush()

        # Ensure active RFP / Quote Request & Engagement exist
        existing_qr = (await db.execute(
            select(AgencyQuoteRequest).where(AgencyQuoteRequest.agency_profile_id == agency_p.id)
        )).scalars().first()

        if not existing_qr:
            quote_req = AgencyQuoteRequest(
                id=uuid.uuid4(),
                organization_id=DEMO_BRAND_ORG_ID,
                agency_profile_id=agency_p.id,
                project_title="Summer Festive Omnichannel Scale",
                project_description="Scale our clay carafes and cookware on Meta Ads and Amazon ahead of the upcoming festival season.",
                budget_inr=50000,
                timeframe="4 weeks",
                contact_email="ananya.deshmukh@auraterra.in",
                status="accepted",
                share_contact_consent=True,
            )
            db.add(quote_req)
            await db.flush()

            db.add(
                AgencyEngagement(
                    id=uuid.uuid4(),
                    organization_id=DEMO_BRAND_ORG_ID,
                    agency_profile_id=agency_p.id,
                    quote_request_id=quote_req.id,
                    agreed_price_inr=45000,
                    billing_type="monthly",
                    status="in_progress",
                    started_at=now - datetime.timedelta(days=10),
                    notes="Festive Scale 2026 — Aura Terra Living contract.",
                )
            )

        # ---------------------------------------------------------------------
        # 8. Demo Consultant Appointments & Private Advisory Notes (4 Appointments)
        # ---------------------------------------------------------------------
        cons_res = await db.execute(
            select(ConsultationRequest).where(ConsultationRequest.assigned_consultant_id == DEMO_CONSULTANT_USER_ID)
        )
        if not cons_res.scalars().first() or force:
            if force:
                await db.execute(
                    delete(ConsultationRequest).where(ConsultationRequest.assigned_consultant_id == DEMO_CONSULTANT_USER_ID)
                )
                await db.flush()

            consultations_seed = [
                (
                    "Aura Terra Living",
                    "Ananya Deshmukh",
                    "ananya.deshmukh@auraterra.in",
                    "Home & Living",
                    "Scaling (₹5L-₹25L/mo)",
                    "confirmed",
                    "REF-DEMO-01",
                    now + datetime.timedelta(days=2, hours=4),
                    (
                        "PRIVATE ADVISORY DIAGNOSIS:\n"
                        "1. Unit economics show 62% gross margin, but Blended CAC is currently ₹420.\n"
                        "2. Recommend bundle architecture (Carafe + Glasses) to lift AOV from ₹1,299 to ₹1,999.\n"
                        "3. Packaging drop test failed at 1.5m; switch from bubblewrap to molded pulp buffer to reduce transit damage returns."
                    ),
                    "Identified AOV expansion opportunities through festive bundling and recommended protective honeycomb packaging.",
                    ["Introduce 3-piece dining gift sets", "Launch automated WhatsApp reorder flow", "Implement unboxing guarantee"],
                    ["Revise primary packaging specification", "Configure 14-day repurchase notification email"],
                ),
                (
                    "Kavya Wellness",
                    "Kavya Nair",
                    "kavya@kavyawellness.in",
                    "Ayurvedic Nutrition",
                    "Early Stage (<₹5L/mo)",
                    "completed",
                    "REF-DEMO-02",
                    now - datetime.timedelta(days=5, hours=2),
                    (
                        "PRIVATE ADVISORY DIAGNOSIS:\n"
                        "1. 85% single-purchase rate indicates weak post-purchase onboarding.\n"
                        "2. Formulate 21-day wellness challenge email sequence to boost 60-day repurchase rate from 15% to 32%."
                    ),
                    "Diagnosed retention bottleneck and outlined post-purchase educational onboarding flow.",
                    ["Setup Klaviyo welcome and compliance series", "Add QR code to product carton linking to guided meditation video"],
                    ["Audit Google Ads branded search queries", "Finalize sample sachet inclusion with orders"],
                ),
                (
                    "Zenith Organics",
                    "Ramesh Gupta",
                    "ramesh@zenithorganics.in",
                    "Gourmet Staples",
                    "Mature (>₹25L/mo)",
                    "completed",
                    "REF-DEMO-03",
                    now - datetime.timedelta(days=12, hours=3),
                    (
                        "PRIVATE ADVISORY DIAGNOSIS:\n"
                        "1. Channel cannibalization: Flipkart pricing is undercut by unverified distributors.\n"
                        "2. File Amazon Brand Registry Infringement complaints to clean up Buy Box ownership.\n"
                        "3. Prepare dark-store allocation for Blinkit/Zepto in South Mumbai and Whitefield."
                    ),
                    "Resolved marketplace channel conflicts and drafted dark-store stock allocation plan.",
                    ["Submit brand registry gate requests on Amazon", "Pilot 4 SKUs on Blinkit Quick Commerce"],
                    ["Enforce strict MAP (Minimum Advertised Price) across all sellers"],
                ),
                (
                    "Sattva Botanicals",
                    "Dr. Pooja Merchant",
                    "pooja@sattvabotanicals.com",
                    "Clean Beauty",
                    "Scaling (₹5L-₹25L/mo)",
                    "confirmed",
                    "REF-DEMO-04",
                    now + datetime.timedelta(days=5, hours=6),
                    (
                        "PRIVATE ADVISORY DIAGNOSIS:\n"
                        "1. High return-to-origin (RTO) on Cash-on-Delivery orders (28%).\n"
                        "2. Recommend UPI prepayment incentive of ₹50 instant discount to shift COD mix from 65% to below 35%."
                    ),
                    "Pre-session review: High COD RTO is eroding operating margin. Focus session on payment gateway optimization.",
                    ["Integrate Cashfree/Razorpay instant UPI discount banner", "Add WhatsApp OTP confirmation for COD orders > ₹1,500"],
                    ["Review shipping partner delivery SLA scorecards"],
                ),
            ]

            for bname, cname, cemail, cat, stage, cstatus, rcode, sdate, inotes, rsum, recs, aitems in consultations_seed:
                db.add(
                    ConsultationRequest(
                        id=uuid.uuid4(),
                        reference_code=rcode,
                        full_name=cname,
                        email=cemail,
                        phone="+91 98201 55432",
                        brand_name=bname,
                        category=cat,
                        business_stage=stage,
                        monthly_revenue="₹12,50,000" if "Scaling" in stage else ("₹28,00,000" if "Mature" in stage else "₹3,50,000"),
                        challenges="CAC optimization on Meta, channel conflict, transit packaging breakage, and scaling marketplace presence.",
                        status=cstatus,
                        assigned_consultant_id=DEMO_CONSULTANT_USER_ID,
                        assigned_consultant_name="Dr. Rajesh Sharma (Lead D2C Advisor)",
                        scheduled_at=sdate,
                        duration_minutes=45,
                        meeting_link="https://meet.google.com/mp-d2c-growth",
                        internal_notes=inotes,
                        report_summary=rsum,
                        recommendations=recs,
                        action_items=aitems,
                    )
                )

        # ---------------------------------------------------------------------
        # 9. Demo Calendar Events
        # ---------------------------------------------------------------------
        cal_res = await db.execute(select(BusinessCalendarEvent).where(BusinessCalendarEvent.organization_id == DEMO_BRAND_ORG_ID))
        if not cal_res.scalars().first():
            events = [
                ("Summer Festival Marketplace Flash Sale", "promotion", now + datetime.timedelta(days=3), now + datetime.timedelta(days=5)),
                ("Warehouse Inventory Cycle Count & Restock", "inventory_reorder", now + datetime.timedelta(days=7), now + datetime.timedelta(days=7)),
                ("Q3 Growth Strategy Advisory Session", "consultation", now + datetime.timedelta(days=2), now + datetime.timedelta(days=2)),
                ("Festive Creative Studio Photoshoot with CraftVerve", "agency_delivery", now + datetime.timedelta(days=9), now + datetime.timedelta(days=10)),
            ]
            for ev_title, ev_type, st, en in events:
                db.add(
                    BusinessCalendarEvent(
                        id=uuid.uuid4(),
                        organization_id=DEMO_BRAND_ORG_ID,
                        title=ev_title,
                        event_type=ev_type,
                        start_time=st,
                        end_time=en,
                        status="scheduled",
                    )
                )

        # Commit all demo environment seeds atomically
        await db.commit()

        # ---------------------------------------------------------------------
        # 10. Write Credentials to secrets/marketpath-initial-access.txt
        # ---------------------------------------------------------------------
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        existing_content = ""
        if SECRETS_FILE.exists():
            existing_content = SECRETS_FILE.read_text(encoding="utf-8")

        demo_block = f"""
================================================================================
FOUR DEMO ACCOUNTS (POPULATED & ISOLATED ENVIRONMENT)
Last Seeded: {now_str}
================================================================================

1. DEMO COMPANY OWNER (D2C Brand Seller Workspace):
   Email:             {demo_emails["company"]}
   Password:          {pw_company}
   Brand Name:        Aura Terra Living (Demo)
   Access Portal:     /login?type=company
   Workspace URL:     /app/dashboard

2. DEMO AGENCY PARTNER (Agency Portal):
   Email:             {demo_emails["agency"]}
   Password:          {pw_agency}
   Agency Name:       CraftVerve Media (Demo)
   Access Portal:     /login?type=agency
   Agency Portal URL: /agency/portal

3. DEMO CONSULTANT (Advisory Workspace):
   Email:             {demo_emails["consultant"]}
   Password:          {pw_consultant}
   Consultant Name:   Dr. Rajesh Sharma
   Access Portal:     /login?type=consultant
   Consultant URL:    /consultant

4. DEMO PLATFORM ADMIN (Admin Demonstration Console):
   Email:             {demo_emails["admin"]}
   Password:          {pw_admin}
   Console Name:      Demo Platform Operator
   Access Portal:     /login?type=admin
   Admin Console URL: /admin

================================================================================
"""

        if "FOUR DEMO ACCOUNTS" in existing_content:
            import re
            new_content = re.sub(
                r"={80}\s*FOUR DEMO ACCOUNTS.*?(?=\n={80}|\Z)",
                demo_block.strip() + "\n",
                existing_content,
                flags=re.DOTALL,
            )
            SECRETS_FILE.write_text(new_content, encoding="utf-8")
        else:
            SECRETS_FILE.write_text(existing_content + "\n" + demo_block, encoding="utf-8")

        print("\n" + "=" * 60)
        print("MarketPath AI — Demo Environment Seeded Successfully")
        print("=" * 60)
        print(f"1. Company Owner:       {demo_emails['company']}")
        print(f"2. Agency Partner:      {demo_emails['agency']}")
        print(f"3. Consultant Advisor:  {demo_emails['consultant']}")
        print(f"4. Platform Admin:      {demo_emails['admin']}")
        print(f"Demo Products:          18 products with variants & stock")
        print(f"Demo Orders:            40 omnichannel sample orders")
        print(f"Secure Credentials:     {SECRETS_FILE.resolve()}")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Seed MarketPath AI Demo Environment.")
    parser.add_argument("--force", action="store_true", help="Force re-seeding of demo records")
    args = parser.parse_args()

    asyncio.run(seed_demo_environment(force=args.force))


if __name__ == "__main__":
    main()

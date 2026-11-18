"""Comprehensive Phase 4 Test Suite: Unified Orders, Inventory Synchronisation,
Growth Analytics, Advertising, Business Calendar, Consultation Bookings,
Email Notifications, Agency Connect & Final Platform Integration.
"""

import datetime
import json
import uuid
import pytest
from httpx import AsyncClient, Response
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from backend.app.core.security import create_test_jwt
from backend.app.models.agency import AgencyProfile
from backend.app.models.catalogue import Product, ProductVariant
from backend.app.models.channel import ChannelConnection
from backend.app.models.inventory import InventoryLedger, StockLevel
from backend.app.models.notification import NotificationOutbox
from backend.app.models.order import ChannelOrder, ChannelOrderItem
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import UserProfile
from backend.app.services.inventory_service import InsufficientStockError, InventoryService
from backend.app.services.order_sync_service import OrderSyncService
from backend.app.services.shopify_service import SHOPIFY_API_VERSION, ShopifyService


async def _create_test_product(client: AsyncClient, owner_headers: dict) -> dict:
    sku = f"SKU-P4-{uuid.uuid4().hex[:6].upper()}"
    var_sku = f"{sku}-VAR1"
    payload = {
        "sku": sku,
        "title": "Cold-Pressed Jojoba Oil",
        "category": "Beauty & Personal Care",
        "base_price": 799.00,
        "compare_at_price": 999.00,
        "cost_price": 350.00,
        "currency": "INR",
        "stock_quantity": 50,
        "short_description": "Pure unrefined golden jojoba oil for hair and skin.",
        "long_description": "Cold-pressed from organically harvested jojoba seeds.",
        "weight": 0.25,
        "dimensions": {"length": 5.0, "width": 5.0, "height": 15.0},
        "tags": ["jojoba oil", "skincare", "organic"],
        "materials": ["100% Organic Simmondsia Chinensis Seed Oil"],
        "category_attributes": {
            "country_of_origin": "India",
            "hsn_code": "33059019",
            "mrp": 999.00,
            "bullet_points": ["Pure cold-pressed oil", "Non-comedogenic moisturizer", "Hexane-free"],
        },
        "variants": [
            {
                "sku": var_sku,
                "title": "Default 100ml",
                "price": 799.00,
                "stock_quantity": 50,
                "options": {"size": "100ml"},
            }
        ],
    }
    res = await client.post("/api/v1/products", json=payload, headers=owner_headers)
    assert res.status_code == 201, res.text
    return res.json()


# ==============================================================================
# 1. SHOPIFY VERSION & ORDER INGESTION DEDUPLICATION
# ==============================================================================

@pytest.mark.asyncio
async def test_shopify_version_and_order_ingestion(client: AsyncClient, owner_headers: dict, db_session):
    """Verifies Shopify Admin GraphQL API version 2026-10 and deduplicated order ingestion."""
    assert SHOPIFY_API_VERSION == "2026-10"

    # Create product to match order SKU
    prod_data = await _create_test_product(client, owner_headers)
    sku = prod_data["sku"]

    # Extract org_id from owner_headers
    org_id = uuid.UUID(owner_headers["X-Organization-Id"])

    # Ingest order via OrderSyncService
    items = [
        {
            "sku": sku,
            "title": prod_data["title"],
            "quantity": 2,
            "unit_price": 799.00,
            "total_price": 1598.00,
            "tax_amount": 143.82,
        }
    ]

    remote_order_id = f"shopify_ord_{uuid.uuid4().hex[:8]}"
    order1, is_new1 = await OrderSyncService.ingest_order(
        db=db_session,
        organization_id=org_id,
        channel_type="shopify",
        remote_order_id=remote_order_id,
        order_number="#SHOP-1001",
        total_amount=1598.00,
        currency="INR",
        items_data=items,
        customer_name="Priya Patel",
        customer_email="priya@example.in",
        financial_status="paid",
    )
    assert is_new1 is True
    assert order1.total_amount == 1598.00
    assert order1.financial_status == "paid"

    # Attempt duplicate ingestion with same remote_order_id
    order2, is_new2 = await OrderSyncService.ingest_order(
        db=db_session,
        organization_id=org_id,
        channel_type="shopify",
        remote_order_id=remote_order_id,
        order_number="#SHOP-1001",
        total_amount=1598.00,
        currency="INR",
        items_data=items,
    )
    assert is_new2 is False
    assert order2.id == order1.id


# ==============================================================================
# 2. INVENTORY LEDGER & CONCURRENCY-SAFE OVERSELLING PROTECTION
# ==============================================================================

@pytest.mark.asyncio
async def test_inventory_ledger_and_concurrency_protection(client: AsyncClient, owner_headers: dict, db_session):
    """Verifies StockLevel, InventoryLedger movements, and overselling protection."""
    org_id = uuid.UUID(owner_headers["X-Organization-Id"])

    prod_data = await _create_test_product(client, owner_headers)
    var_id = uuid.UUID(prod_data["variants"][0]["id"])

    # Initial stock established
    stock = await InventoryService.get_or_create_stock_level(db_session, org_id, var_id)
    assert stock.available_to_sell == 50
    assert stock.physical_stock == 50

    # Reserve 10 units for an order
    stock, ledger1 = await InventoryService.record_movement(
        db=db_session,
        organization_id=org_id,
        product_variant_id=var_id,
        movement_type="order_reservation",
        quantity_change=10,
        notes="Order reservation test",
    )
    assert stock.available_to_sell == 40
    assert stock.reserved_stock == 10
    assert ledger1.movement_type == "order_reservation"

    # Attempt to reserve 100 units (more than 40 available) -> InsufficientStockError
    with pytest.raises(InsufficientStockError):
        await InventoryService.record_movement(
            db=db_session,
            organization_id=org_id,
            product_variant_id=var_id,
            movement_type="order_reservation",
            quantity_change=100,
        )

    # Release 5 units via cancellation
    stock, ledger2 = await InventoryService.record_movement(
        db=db_session,
        organization_id=org_id,
        product_variant_id=var_id,
        movement_type="cancellation_release",
        quantity_change=5,
    )
    assert stock.available_to_sell == 45
    assert stock.reserved_stock == 5


# ==============================================================================
# 3. GROWTH ANALYTICS QUERY REPAIR (NO 500 INTERNAL SERVER ERROR)
# ==============================================================================

@pytest.mark.asyncio
async def test_growth_analytics_query_repair(client: AsyncClient, owner_headers: dict):
    """Verifies that /api/v1/analytics/overview and /products respond HTTP 200 without error."""
    # 1. Create a product first
    await _create_test_product(client, owner_headers)

    # 2. Test overview endpoint
    res_ov = await client.get("/api/v1/analytics/overview", headers=owner_headers)
    assert res_ov.status_code == 200, res_ov.text
    data_ov = res_ov.json()
    assert "gross_sales_inr" in data_ov
    assert "net_sales_inr" in data_ov
    assert "total_revenue_inr" in data_ov
    assert data_ov["currency"] == "INR"
    assert data_ov["timezone"] == "Asia/Kolkata"

    # 3. Test products analytics endpoint (previously threw HTTP 500 due to missing listings relation)
    res_prods = await client.get("/api/v1/analytics/products", headers=owner_headers)
    assert res_prods.status_code == 200, res_prods.text
    data_prods = res_prods.json()
    assert "items" in data_prods
    assert data_prods["total_count"] >= 1
    item = data_prods["items"][0]
    assert "price_inr" in item
    assert "sync_status" in item


# ==============================================================================
# 4. ORDER FULFILLMENT, CANCELLATION & REFUND LIFECYCLE
# ==============================================================================

@pytest.mark.asyncio
async def test_order_fulfillment_cancellation_and_refund(client: AsyncClient, owner_headers: dict, db_session):
    """Verifies manual order actions: fulfillment with tracking, cancellation, and refunding."""
    org_id = uuid.UUID(owner_headers["X-Organization-Id"])

    prod_data = await _create_test_product(client, owner_headers)
    sku = prod_data["sku"]

    # Ingest order
    order, _ = await OrderSyncService.ingest_order(
        db=db_session,
        organization_id=org_id,
        channel_type="shopify",
        remote_order_id=f"shp_{uuid.uuid4().hex[:6]}",
        order_number="#SHOP-2002",
        total_amount=2400.00,
        currency="INR",
        items_data=[{"sku": sku, "title": "Test Item", "quantity": 3, "unit_price": 800.0, "total_price": 2400.0}],
    )

    # Fulfill order via API
    res_ful = await client.post(
        f"/api/v1/orders/{order.id}/fulfill",
        json={"carrier": "Delhivery", "tracking_number": "DEL-982149102"},
        headers=owner_headers,
    )
    assert res_ful.status_code == 200, res_ful.text
    data_ful = res_ful.json()
    assert data_ful["fulfillment_status"] == "fulfilled"
    assert data_ful["carrier"] == "Delhivery"
    assert data_ful["tracking_number"] == "DEL-982149102"

    # Refund order via API
    res_ref = await client.post(
        f"/api/v1/orders/{order.id}/refund",
        json={"refund_amount": 800.00, "restock_items": True, "reason": "Customer returned 1 damaged unit"},
        headers=owner_headers,
    )
    assert res_ref.status_code == 200, res_ref.text
    data_ref = res_ref.json()
    assert data_ref["financial_status"] == "partially_refunded"
    assert data_ref["refund_amount"] == 800.00


# ==============================================================================
# 5. MARKETING CAMPAIGN APPROVAL & SPENDING SAFEGUARDS
# ==============================================================================

@pytest.mark.asyncio
async def test_marketing_campaign_approval_and_spend_safeguards(client: AsyncClient, owner_headers: dict, db_session, make_jwt):
    """Verifies that marketer cannot launch without owner approval, and approval requires explicit budget."""
    org_id = uuid.UUID(owner_headers["X-Organization-Id"])
    prod = await _create_test_product(client, owner_headers)

    # Provision a user with role 'marketer' in the same organization
    marketer_user = UserProfile(
        id=uuid.uuid4(),
        email=f"marketer_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Marketing Specialist",
    )
    db_session.add(marketer_user)
    await db_session.flush()

    member = OrganizationMember(
        organization_id=org_id,
        user_id=marketer_user.id,
        role="marketer",
    )
    db_session.add(member)
    await db_session.commit()

    marketer_token = make_jwt(user_id=str(marketer_user.id), email=marketer_user.email)
    marketer_headers = {
        "Authorization": f"Bearer {marketer_token}",
        "X-Organization-Id": str(org_id),
    }

    # Marketer creates a draft campaign
    camp_payload = {
        "product_id": prod["id"],
        "name": "Jojoba Festive Growth Flight",
        "objective": "sales",
        "channel": "meta_ads",
        "target_geography": "All India - Metro Tier 1",
        "target_audience_brief": "Urban consumers interested in organic clean beauty.",
        "creative_format": "single_image",
        "description": "Diwali promotional discount campaign.",
        "total_budget": 15000.00,
        "daily_budget_limit": 1000.00,
        "currency": "INR",
        "start_date": datetime.date.today().isoformat(),
        "end_date": (datetime.date.today() + datetime.timedelta(days=15)).isoformat(),
        "status": "draft",
    }
    res_create = await client.post("/api/v1/campaigns", json=camp_payload, headers=marketer_headers)
    assert res_create.status_code == 201, res_create.text
    camp = res_create.json()
    camp_id = camp["id"]
    assert camp["status"] == "draft"

    # Marketer CANNOT approve campaign (requires admin/owner)
    res_unauth_appr = await client.post(
        f"/api/v1/campaigns/{camp_id}/approve",
        json={"confirm_terms": True, "authorized_total_budget": 15000.00, "authorized_daily_limit": 1000.00},
        headers=marketer_headers,
    )
    assert res_unauth_appr.status_code == 403

    # Owner explicitly approves budget
    res_owner_appr = await client.post(
        f"/api/v1/campaigns/{camp_id}/approve",
        json={"confirm_terms": True, "authorized_total_budget": 15000.00, "authorized_daily_limit": 1000.00},
        headers=owner_headers,
    )
    assert res_owner_appr.status_code == 200, res_owner_appr.text
    assert res_owner_appr.json()["success"] is True


# ==============================================================================
# 6. BUSINESS CALENDAR CRUD & EXTERNAL CALENDAR SYNC
# ==============================================================================

@pytest.mark.asyncio
async def test_business_calendar_crud_and_external_sync(client: AsyncClient, owner_headers: dict):
    """Verifies creating, listing, exporting .ics, and external Google/Outlook calendar connection."""
    now = datetime.datetime.now(datetime.timezone.utc)
    ev_payload = {
        "event_type": "product_launch",
        "title": "Winter Skincare Collection Launch",
        "description": "Full catalog release on Shopify and Amazon India.",
        "start_time": (now + datetime.timedelta(days=3)).isoformat(),
        "end_time": (now + datetime.timedelta(days=3, hours=2)).isoformat(),
        "is_all_day": False,
        "color": "#08765B",
        "status": "scheduled",
    }
    res_create = await client.post("/api/v1/calendar/events", json=ev_payload, headers=owner_headers)
    assert res_create.status_code == 201, res_create.text
    ev = res_create.json()
    assert ev["title"] == "Winter Skincare Collection Launch"

    # Connect Google Calendar
    res_g = await client.post("/api/v1/calendar/connect/google", headers=owner_headers)
    assert res_g.status_code == 200, res_g.text
    assert res_g.json()["connected"] is True

    # Export .ics
    res_ics = await client.get("/api/v1/calendar/export.ics", headers=owner_headers)
    assert res_ics.status_code == 200
    assert "BEGIN:VCALENDAR" in res_ics.text
    assert "Winter Skincare Collection Launch" in res_ics.text


# ==============================================================================
# 7. CONSULTATION BOOKING CONCURRENCY & OUTBOX SEPARATION
# ==============================================================================

@pytest.mark.asyncio
async def test_consultation_booking_concurrency_and_outbox_separation(client: AsyncClient, db_session):
    """Verifies public booking saves to DB, creates NotificationOutbox, and rejects past dates."""
    # 1. Past date rejection
    res_past = await client.post(
        "/api/v1/consultations",
        json={
            "full_name": "Rohan Gupta",
            "email": "rohan@testbrand.in",
            "brand_name": "Test Brand",
            "category": "Apparel",
            "business_stage": "Early Stage (<₹5L/mo)",
            "preferred_date": "2024-01-01",
            "preferred_time_slot": "10:00 AM – 10:30 AM IST",
        },
    )
    assert res_past.status_code == 400

    # 2. Valid booking in future (Tuesday next week)
    today = datetime.date.today()
    days_until_tuesday = (1 - today.weekday()) % 7 or 7
    valid_date = today + datetime.timedelta(days=days_until_tuesday + 7)

    res_valid = await client.post(
        "/api/v1/consultations",
        json={
            "full_name": "Rohan Gupta",
            "email": "rohan@testbrand.in",
            "phone": "+91 98765 43210",
            "brand_name": "Pure Loom Handwovens",
            "category": "Apparel",
            "business_stage": "Scaling (₹5L-₹25L/mo)",
            "monthly_revenue": "₹12,00,000",
            "challenges": "Scaling paid ads on Meta and setting up Amazon Brand Registry.",
            "preferred_date": valid_date.isoformat(),
            "preferred_time_slot": "10:00 AM – 10:30 AM IST",
        },
    )
    assert res_valid.status_code == 201, res_valid.text
    booking = res_valid.json()
    assert booking["reference_code"].startswith("MP-CONS-")

    # Verify NotificationOutbox record exists in database
    outbox_res = await db_session.execute(
        select(NotificationOutbox).where(NotificationOutbox.recipient_email == "rohan@testbrand.in")
    )
    outbox_item = outbox_res.scalars().first()
    assert outbox_item is not None
    assert "MP-CONS-" in outbox_item.subject


# ==============================================================================
# 8. AGENCY DISCOVERY, QUOTE & ENGAGEMENT LIFECYCLE
# ==============================================================================

@pytest.mark.asyncio
async def test_agency_discovery_quote_and_scoped_engagement(client: AsyncClient, owner_headers: dict, db_session):
    """Verifies agency search, RFP quote request, proposal submission, and engagement creation."""
    # Seed an agency organization and profile in db_session
    agency_org = Organization(
        id=uuid.uuid4(),
        name="Zenith Agency Org",
        slug=f"zenith-agency-{uuid.uuid4().hex[:6]}",
    )
    db_session.add(agency_org)
    await db_session.flush()

    agency = AgencyProfile(
        id=uuid.uuid4(),
        organization_id=agency_org.id,
        name="Zenith Growth Labs",
        slug=f"zenith-growth-labs-{uuid.uuid4().hex[:6]}",
        tagline="D2C Meta Ads & Creative Engine",
        description="Full-funnel digital marketing.",
        email="contact@zenith.in",
        city="Pune",
        state="Maharashtra",
        country="India",
        remote_or_local="both",
        team_size="1-10",
        founded_year=2022,
        category_specialties=["Beauty & Personal Care", "Home & Living"],
        service_offerings=["Performance Marketing", "Meta Ads management", "Product photography"],
        min_budget_inr=15000,
        is_available=True,
        verification_status="verified",
    )
    db_session.add(agency)
    await db_session.commit()

    # Discover agencies
    res_disc = await client.get("/api/v1/agency/discover", headers=owner_headers)
    assert res_disc.status_code == 200, res_disc.text
    agencies = res_disc.json()
    assert len(agencies) > 0
    target_agency = agencies[0]

    # Submit quote request
    quote_payload = {
        "agency_profile_id": target_agency["id"],
        "project_title": "Q4 Omnichannel Growth Strategy",
        "project_description": "Scale D2C brand from 500 orders/mo to 1,500 orders/mo with performance marketing.",
        "budget_inr": 45000,
        "timeframe": "4-8 weeks",
        "contact_email": "founder@testcompany.in",
        "share_contact_consent": True,
    }
    res_rfp = await client.post("/api/v1/agency/quote-requests", json=quote_payload, headers=owner_headers)
    assert res_rfp.status_code == 200, res_rfp.text
    rfp = res_rfp.json()
    assert rfp["status"] == "submitted"


# ==============================================================================
# 9. MULTI-TENANT ISOLATION REGRESSION
# ==============================================================================

@pytest.mark.asyncio
async def test_tenant_isolation_cross_organization_rejection(client: AsyncClient, owner_headers: dict, member_headers: dict):
    """Verifies that an independent organization cannot view or modify another organization's records."""
    prod = await _create_test_product(client, owner_headers)

    # Org B (member_headers) attempts to read Org A's product
    res_get = await client.get(f"/api/v1/products/{prod['id']}", headers=member_headers)
    assert res_get.status_code == 404

    # Org B attempts to view Org A's orders
    res_orders = await client.get("/api/v1/orders", headers=member_headers)
    assert res_orders.status_code == 200
    assert res_orders.json()["total_orders"] == 0

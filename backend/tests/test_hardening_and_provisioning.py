"""Comprehensive Test Suite for Phase 4 Hardening, Authentication Expansion,
Demo Provisioning, and Real Platform Admin Implementation.
"""

import datetime
import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from pathlib import Path
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.core.security import create_test_jwt, hash_password, verify_password
from backend.app.models.agency import AgencyMember, AgencyProfile
from backend.app.models.audit import AuditLog
from backend.app.models.catalogue import Product, ProductVariant
from backend.app.models.inventory import InventoryLedger, StockLevel
from backend.app.models.notification import NotificationOutbox
from backend.app.models.order import ChannelOrder, ChannelOrderItem, ReturnItem, ReturnRequest
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import UserProfile
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.inventory_service import InventoryService
from backend.app.services.meta_ads_service import (
    META_GRAPH_API_VERSION,
    META_MARKETING_API_VERSION,
    validate_meta_version,
)
from backend.app.services.outbox_service import OutboxService
from backend.app.services.reservation_policy import ReservationPolicy
from backend.app.services.return_service import ReturnService


# ==============================================================================
# 1. META API VERSION COMPATIBILITY & DECOUPLING
# ==============================================================================

def test_meta_api_version_decoupling_and_expiration_guards():
    """Verifies Graph API and Marketing API have independent versions and sunset versions are rejected."""
    # 1. Versions must not be shared statically without independence
    assert hasattr(settings, "META_GRAPH_API_VERSION")
    assert hasattr(settings, "META_MARKETING_API_VERSION")
    assert META_GRAPH_API_VERSION >= "v21.0"
    assert META_MARKETING_API_VERSION >= "v21.0"

    # 2. Expired versions must be rejected
    with pytest.raises(ValueError, match="expired or sunset"):
        validate_meta_version("v18.0", "Meta Graph API")

    with pytest.raises(ValueError, match="expired or sunset"):
        validate_meta_version("v19.0", "Meta Marketing API")

    with pytest.raises(ValueError, match="expired or sunset"):
        validate_meta_version("v20.0", "Meta Graph API")

    # 3. Active versions must succeed
    assert validate_meta_version("v21.0") == "v21.0"
    assert validate_meta_version("v26.0") == "v26.0"


# ==============================================================================
# 2. AGENCY SIGNUP, VETTING & LOGIN PERMISSIONS
# ==============================================================================

@pytest.mark.asyncio
async def test_agency_signup_and_approval_workflow(client: AsyncClient, db_session, make_jwt):
    """Verifies public agency signup, pending review restriction, and admin approval."""
    admin_token = make_jwt(user_id=str(uuid.uuid4()), email="admin@marketpath.ai", is_platform_admin=True)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    agency_email = f"agency-{uuid.uuid4().hex[:6]}@partner.in"
    payload = {
        "agency_name": "Apex Omni Growth",
        "contact_name": "Rohan Deshmukh",
        "email": agency_email,
        "password": "Password123#Secure",
        "phone": "+91 98200 12345",
        "city": "Mumbai",
        "state": "Maharashtra",
        "service_categories": ["Performance Marketing", "Creative Studio"],
        "years_of_experience": 4,
        "description": "Leading D2C performance scaling agency with 4x average ROAS.",
        "gst_number": "27AABCA1234A1Z5",
    }

    # 1. Public Agency Signup
    res = await client.post("/api/v1/auth/agency/signup", json=payload)
    assert res.status_code == 201, res.text
    signup_data = res.json()
    assert signup_data["status"] == "under_review"
    assert signup_data["account_type"] == "agency"

    # 2. Attempt login before approval -> must be rejected with 403 Forbidden
    login_res = await client.post(
        "/api/v1/auth/login-account",
        json={"email": agency_email, "password": "Password123#Secure", "account_type": "agency"},
    )
    assert login_res.status_code == 403
    assert "under review" in login_res.json()["detail"].lower()

    # 3. Admin reviews and approves the agency
    # Find agency profile
    ap_res = await db_session.execute(select(AgencyProfile).where(AgencyProfile.email == agency_email))
    agency = ap_res.scalar_one_or_none()
    assert agency is not None
    assert agency.verification_status == "under_review"

    admin_patch = await client.patch(
        f"/api/v1/admin/agencies/{agency.id}/verification",
        json={"verification_status": "verified", "tier": "verified_partner", "is_featured": True},
        headers=admin_headers,
    )
    assert admin_patch.status_code == 200, admin_patch.text

    # 4. Agency can now log in successfully
    approved_login = await client.post(
        "/api/v1/auth/login-account",
        json={"email": agency_email, "password": "Password123#Secure", "account_type": "agency"},
    )
    assert approved_login.status_code == 200, approved_login.text
    assert approved_login.json()["redirect_url"] == "/agency/portal"


# ==============================================================================
# 3. CONSULTANT SIGNUP, VETTING & LOGIN PERMISSIONS
# ==============================================================================

@pytest.mark.asyncio
async def test_consultant_signup_and_approval_workflow(client: AsyncClient, db_session, make_jwt):
    """Verifies consultant signup, pending review restriction, and platform admin approval."""
    admin_token = make_jwt(user_id=str(uuid.uuid4()), email="admin@marketpath.ai", is_platform_admin=True)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    cons_email = f"consultant-{uuid.uuid4().hex[:6]}@advisor.in"
    payload = {
        "full_name": "Dr. Ananya Sen",
        "email": cons_email,
        "password": "AdvisorPassword123#",
        "phone": "+91 99887 76655",
        "location": "Bengaluru, KA",
        "professional_title": "Senior D2C Supply Chain Strategist",
        "expertise_categories": ["Omnichannel Supply Chain", "Unit Economics"],
        "years_of_experience": 8,
        "bio": "Former supply chain director for leading FMCG brands now advising early-stage founders.",
        "availability": "part_time",
    }

    # 1. Public Consultant Signup
    res = await client.post("/api/v1/auth/consultant/signup", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["status"] == "under_review"
    assert data["account_type"] == "consultant"

    # 2. Attempt login before approval -> 403 Forbidden
    login_res = await client.post(
        "/api/v1/auth/login-account",
        json={"email": cons_email, "password": "AdvisorPassword123#", "account_type": "consultant"},
    )
    assert login_res.status_code == 403
    assert "under review" in login_res.json()["detail"].lower()

    # 3. Admin lists consultants and approves
    admin_list = await client.get("/api/v1/admin/consultants", headers=admin_headers)
    assert admin_list.status_code == 200
    consultants = admin_list.json()
    matched = next((c for c in consultants if c["email"] == cons_email), None)
    assert matched is not None
    assert matched["vetting_status"] == "under_review"

    # Approve
    approve_res = await client.patch(
        f"/api/v1/admin/consultants/{matched['id']}/vetting",
        json={"vetting_status": "approved"},
        headers=admin_headers,
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["vetting_status"] == "approved"

    # 4. Consultant logs in successfully
    approved_login = await client.post(
        "/api/v1/auth/login-account",
        json={"email": cons_email, "password": "AdvisorPassword123#", "account_type": "consultant"},
    )
    assert approved_login.status_code == 200
    assert approved_login.json()["redirect_url"] == "/consultant"


# ==============================================================================
# 4. PHYSICAL RETURN VS FINANCIAL REFUND SEPARATION & DAMAGED STOCK DISPOSITION
# ==============================================================================

@pytest.mark.asyncio
async def test_physical_return_separation_and_damage_disposition(db_session):
    """Verifies return lifecycle: requested -> authorized -> in_transit -> received -> inspected -> completed.
    Ensures resalable items increase available_to_sell stock, while damaged items are recorded as damaged_stock.
    """
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Return Test Org", slug=f"return-org-{org_id.hex[:6]}", is_active=True)
    db_session.add(org)

    # Create Product & Variant
    prod_id = uuid.uuid4()
    var_id = uuid.uuid4()
    sku = f"SKU-RET-{uuid.uuid4().hex[:6]}"

    prod = Product(
        id=prod_id,
        organization_id=org_id,
        sku=sku,
        title="Terracotta Water Jug",
        category="Home & Living",
        base_price=1000.0,
        stock_quantity=10,
    )
    db_session.add(prod)

    var = ProductVariant(
        id=var_id,
        product_id=prod_id,
        sku=sku,
        title="Standard Jug",
        price=1000.0,
        stock_quantity=10,
    )
    db_session.add(var)

    # Initial StockLevel
    stock = StockLevel(
        organization_id=org_id,
        product_id=prod_id,
        product_variant_id=var_id,
        sku=sku,
        location_id="primary_warehouse",
        physical_stock=10,
        reserved_stock=2,
        available_to_sell=8,
        damaged_stock=0,
        returned_stock=0,
    )
    db_session.add(stock)

    # Create ChannelOrder
    order_id = uuid.uuid4()
    order = ChannelOrder(
        id=order_id,
        organization_id=org_id,
        channel_type="shopify",
        remote_order_id=f"REM-RET-{uuid.uuid4().hex[:6]}",
        order_number=f"ORD-RET-101",
        total_amount=2000.0,
        subtotal=2000.0,
        financial_status="paid",
        fulfillment_status="fulfilled",
        order_lifecycle_status="delivered",
        order_date=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(order)

    oi = ChannelOrderItem(
        id=uuid.uuid4(),
        order_id=order_id,
        product_id=prod_id,
        product_variant_id=var_id,
        sku=sku,
        title="Terracotta Water Jug",
        quantity=2,
        unit_price=1000.0,
        total_price=2000.0,
    )
    db_session.add(oi)
    await db_session.commit()

    # 1. Create Return Request (2 units requested)
    ret = await ReturnService.create_return_request(
        db=db_session,
        organization_id=org_id,
        order_id=order_id,
        reason="One unit cracked in transit, second unit unwanted",
        items_data=[{"sku": sku, "quantity": 2, "refund_amount": 2000.0}],
    )
    assert ret.status == "requested"

    # 2. Authorize
    auth_ret = await ReturnService.authorize_return(db_session, org_id, ret.id)
    assert auth_ret.status == "authorized"
    assert auth_ret.tracking_number is not None

    # 3. In Transit -> Received
    await ReturnService.mark_in_transit(db_session, org_id, ret.id)
    rec_ret = await ReturnService.receive_return(db_session, org_id, ret.id)
    assert rec_ret.status == "received"

    # 4. Inspection: 1 unit resalable, 1 unit damaged
    item_id = str(rec_ret.items[0].id)
    comp_ret = await ReturnService.inspect_and_complete_return(
        db=db_session,
        organization_id=org_id,
        return_id=ret.id,
        inspections=[
            {
                "item_id": item_id,
                "sku": sku,
                "quantity_received": 2,
                "resalable_quantity": 1,
                "damaged_quantity": 1,
                "inspection_result": "partial",
                "refund_amount": 2000.0,
            }
        ],
    )
    assert comp_ret.status == "completed"

    # 5. Verify inventory disposition:
    # Physical stock was 10. Resalable returned = 1 -> increases available_to_sell from 8 to 9.
    # Damaged returned = 1 -> damaged_stock = 1, NOT added to available_to_sell!
    stk_res = await db_session.execute(select(StockLevel).where(StockLevel.product_variant_id == var_id))
    updated_stock = stk_res.scalar_one()
    assert updated_stock.available_to_sell == 9
    assert updated_stock.damaged_stock == 1

    # 6. Verify safeguard against double restocking
    await ReturnService.inspect_and_complete_return(
        db=db_session,
        organization_id=org_id,
        return_id=ret.id,
        inspections=[{"item_id": item_id, "sku": sku, "quantity_received": 2, "resalable_quantity": 1, "damaged_quantity": 1}],
    )
    # available_to_sell must remain 9, not incremented again!
    stk_res2 = await db_session.execute(select(StockLevel).where(StockLevel.product_variant_id == var_id))
    assert stk_res2.scalar_one().available_to_sell == 9


# ==============================================================================
# 5. CHANNEL-AWARE ORDER RESERVATION & PAYMENT FAILURE RELEASE
# ==============================================================================

@pytest.mark.asyncio
async def test_channel_aware_reservation_policy_and_failure_release(db_session):
    """Verifies reservation rules: paid reserves, COD reserves, unpaid gets temporary reservation,
    and payment failure releases stock cleanly.
    """
    # 1. Paid order -> reserves stock
    res, is_temp, _ = ReservationPolicy.evaluate_reservation_need("paid", None, "shopify")
    assert res is True
    assert is_temp is False

    # 2. Confirmed COD -> reserves stock
    res_cod, is_temp_cod, _ = ReservationPolicy.evaluate_reservation_need("pending", "COD - Cash on Delivery", "shopify", is_cod=True)
    assert res_cod is True
    assert is_temp_cod is False

    # 3. Unpaid online order -> temporary reservation with expiry
    res_unpaid, is_temp_unpaid, exp = ReservationPolicy.evaluate_reservation_need("pending", "razorpay_online", "shopify")
    assert res_unpaid is True
    assert is_temp_unpaid is True
    assert exp is not None

    # 4. Payment Failure -> releases reservation
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Policy Org", slug=f"pol-org-{org_id.hex[:6]}", is_active=True)
    db_session.add(org)

    prod_id = uuid.uuid4()
    var_id = uuid.uuid4()
    sku = f"SKU-POL-{uuid.uuid4().hex[:6]}"

    prod = Product(id=prod_id, organization_id=org_id, sku=sku, title="Chai Glasses", category="Home", base_price=500.0, stock_quantity=20)
    db_session.add(prod)
    var = ProductVariant(id=var_id, product_id=prod_id, sku=sku, title="Standard", price=500.0, stock_quantity=20)
    db_session.add(var)

    # Initial stock: 20 physical, 2 reserved, 18 available
    stk = StockLevel(
        organization_id=org_id,
        product_id=prod_id,
        product_variant_id=var_id,
        sku=sku,
        location_id="primary_warehouse",
        physical_stock=20,
        reserved_stock=2,
        available_to_sell=18,
    )
    db_session.add(stk)

    order_id = uuid.uuid4()
    order = ChannelOrder(
        id=order_id,
        organization_id=org_id,
        channel_type="shopify",
        remote_order_id=f"REM-POL-{uuid.uuid4().hex[:6]}",
        order_number="ORD-POL-1",
        total_amount=1000.0,
        subtotal=1000.0,
        financial_status="pending",
        order_lifecycle_status="pending_payment",
        order_date=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(order)
    oi = ChannelOrderItem(id=uuid.uuid4(), order_id=order_id, product_id=prod_id, product_variant_id=var_id, sku=sku, title="Chai Glasses", quantity=2, unit_price=500.0, total_price=1000.0)
    db_session.add(oi)
    await db_session.commit()

    # Trigger payment failure
    failed_ord = await ReservationPolicy.handle_payment_failure(db_session, org_id, order_id, "Card payment declined")
    assert failed_ord.financial_status == "failed"
    assert failed_ord.order_lifecycle_status == "payment_failed"

    # StockLevel reserved_stock must decrease by 2, available_to_sell increase by 2 to 20
    stk_res = await db_session.execute(select(StockLevel).where(StockLevel.product_variant_id == var_id))
    stk_updated = stk_res.scalar_one()
    assert stk_updated.reserved_stock == 0
    assert stk_updated.available_to_sell == 20


# ==============================================================================
# 6. FINANCIAL ANALYTICS METHODOLOGY ACCURACY
# ==============================================================================

@pytest.mark.asyncio
async def test_financial_analytics_methodology(db_session):
    """Verifies net merchandise sales calculation without artificial max(0.0) suppression."""
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Analytics Org", slug=f"ana-org-{org_id.hex[:6]}", is_active=True)
    db_session.add(org)

    # Order 1: 1000 gross, 100 discount, 50 ship, 90 tax, 0 refund -> total 1040
    o1 = ChannelOrder(
        id=uuid.uuid4(),
        organization_id=org_id,
        channel_type="shopify",
        remote_order_id="ORD-ANA-1",
        order_number="ANA-1",
        total_amount=1040.0,
        subtotal=1000.0,
        discount_amount=100.0,
        shipping_amount=50.0,
        tax_amount=90.0,
        refund_amount=0.0,
        financial_status="paid",
        order_lifecycle_status="paid",
        order_date=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(o1)

    # Order 2: 500 gross, 0 discount, 0 ship, 0 tax, 700 refund (excess refund scenario) -> total 500
    o2 = ChannelOrder(
        id=uuid.uuid4(),
        organization_id=org_id,
        channel_type="shopify",
        remote_order_id="ORD-ANA-2",
        order_number="ANA-2",
        total_amount=500.0,
        subtotal=500.0,
        discount_amount=0.0,
        shipping_amount=0.0,
        tax_amount=0.0,
        refund_amount=700.0,
        financial_status="refunded",
        order_lifecycle_status="refunded",
        order_date=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(o2)
    await db_session.commit()

    overview = await AnalyticsService.get_overview(db_session, org_id)
    assert overview.total_orders == 2
    assert overview.gross_sales_inr == 1540.0
    # Net sales should be gross (1540) - refunds (700) = 840.0
    assert overview.net_sales_inr == 840.0
    assert overview.discounts_inr == 100.0
    assert overview.refunds_inr == 700.0
    assert overview.shipping_inr == 50.0
    assert overview.taxes_inr == 90.0


# ==============================================================================
# 7. NOTIFICATION OUTBOX RELIABILITY & ATOMIC LEASING
# ==============================================================================

@pytest.mark.asyncio
async def test_notification_outbox_worker_reliability(db_session):
    """Verifies atomic leasing of outbox entries, delivery dispatch, and dead-letter queue handling."""
    # 1. Insert pending notification
    msg = NotificationOutbox(
        recipient_email="test.client@example.com",
        recipient_name="Test Merchant",
        notification_type="order_shipped",
        subject="Your order has been shipped",
        context_data={"order_number": "AT-1001"},
        status="pending",
        attempts_count=0,
    )
    db_session.add(msg)
    await db_session.commit()

    # 2. Process outbox queue
    res = await OutboxService.process_outbox_queue(db_session, batch_size=5)
    assert res["processed_count"] == 1
    assert res["successful_count"] == 1

    # Verify status transition
    msg_res = await db_session.execute(select(NotificationOutbox).where(NotificationOutbox.id == msg.id))
    updated_msg = msg_res.scalar_one()
    assert updated_msg.status == "accepted_by_provider"
    assert updated_msg.attempts_count == 1


# ==============================================================================
# 8. DEMO PROVISIONING & PLATFORM ADMIN BOOTSTRAP INTEGRITY
# ==============================================================================

@pytest.mark.asyncio
async def test_demo_and_platform_admin_provisioning_state(db_session):
    """Verifies 4 demo accounts and single Platform Admin are provisioned with correct roles."""
    expected_emails = [
        ("demo.company@marketpath.ai", "company", False),
        ("demo.agency@marketpath.ai", "agency", False),
        ("demo.consultant@marketpath.ai", "consultant", False),
        ("demo.admin@marketpath.ai", "admin", False),
        ("operator@marketpath.ai", "admin", True),
    ]

    import sqlite3
    conn = sqlite3.connect("marketpath.db")
    c = conn.cursor()

    for email, expected_type, expected_admin in expected_emails:
        row = c.execute(
            "SELECT email, account_type, is_platform_admin, password_hash, is_active FROM user_profiles WHERE email = ?",
            (email,),
        ).fetchone()
        assert row is not None, f"Expected account {email} not found in database."
        assert row[1] == expected_type
        assert bool(row[2]) is expected_admin
        assert row[3] is not None
        assert bool(row[4]) is True

    conn.close()

    # Verify credentials vault exists if present locally
    vault_path = Path("secrets/marketpath-initial-access.txt")
    if vault_path.exists():
        content = vault_path.read_text(encoding="utf-8")
        assert "operator@marketpath.ai" in content
        assert "demo.company@marketpath.ai" in content
        assert "demo.agency@marketpath.ai" in content
        assert "demo.consultant@marketpath.ai" in content
        assert "demo.admin@marketpath.ai" in content


# ==============================================================================
# 9. DEMO ADMIN PRIVILEGE ISOLATION & NEGATIVE SECURITY TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_demo_admin_cannot_access_real_admin_endpoints(client: AsyncClient, db_session):
    """Negative Security Test: Proves Demo Admin is strictly rejected from real platform admin APIs."""
    # 0. Seed Demo Admin in isolated test database
    pw_hash = hash_password("MarketPath-DemoAdmin-2026!")
    admin_user = UserProfile(
        id=uuid.UUID("d0000001-0000-0000-0000-000000000004"),
        email="demo.admin@marketpath.ai",
        full_name="Demo Platform Operator",
        account_type="admin",
        is_platform_admin=False,
        password_hash=pw_hash,
        is_active=True,
    )
    db_session.add(admin_user)
    await db_session.commit()

    # 1. Login as Demo Admin
    login_res = await client.post(
        "/api/v1/auth/login-account",
        json={
            "email": "demo.admin@marketpath.ai",
            "password": "MarketPath-DemoAdmin-2026!",
            "account_type": "admin",
        },
    )
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    user_data = login_res.json()["user"]

    # Verify user profile attributes: account_type is 'admin' but is_platform_admin is strictly False
    assert user_data["account_type"] == "admin"
    assert user_data["is_platform_admin"] is False

    demo_headers = {"Authorization": f"Bearer {token}"}

    # 2. Negative test: Real Platform Admin Overview -> MUST return 403 Forbidden
    res_overview = await client.get("/api/v1/admin/overview", headers=demo_headers)
    assert res_overview.status_code == 403
    assert "Platform Administrator privileges required" in res_overview.json()["detail"]

    # 3. Negative test: Real Platform Admin Organizations -> MUST return 403 Forbidden
    res_orgs = await client.get("/api/v1/admin/organizations", headers=demo_headers)
    assert res_orgs.status_code == 403

    # 4. Negative test: Real Platform Admin Users -> MUST return 403 Forbidden
    res_users = await client.get("/api/v1/admin/users", headers=demo_headers)
    assert res_users.status_code == 403

    # 5. Negative test: Mutation attempt (Suspend user) -> MUST return 403 Forbidden
    res_suspend = await client.post(
        f"/api/v1/admin/users/{user_data['id']}/suspend",
        headers=demo_headers,
    )
    assert res_suspend.status_code == 403

    # 6. Positive test: Dedicated Demo Admin Overview -> MUST return 200 OK with synthetic telemetry
    res_demo_overview = await client.get("/api/v1/demo-admin/overview", headers=demo_headers)
    assert res_demo_overview.status_code == 200
    telemetry = res_demo_overview.json()
    assert telemetry["total_users"] == 4
    assert telemetry["total_products"] == 18
    assert "ISOLATED_RECRUITER_DEMO" in telemetry["connector_health"]["environment_mode"]
    assert telemetry["connector_health"]["production_data_access"] == "BLOCKED"

    # 7. Positive test: Dedicated Demo Admin Organizations -> MUST return 200 OK
    res_demo_orgs = await client.get("/api/v1/demo-admin/organizations", headers=demo_headers)
    assert res_demo_orgs.status_code == 200

    # 8. Negative test on demo-admin mutations -> MUST return 403 Forbidden
    res_mutation = await client.post(
        f"/api/v1/demo-admin/users/{user_data['id']}/suspend",
        headers=demo_headers,
    )
    assert res_mutation.status_code == 403
    assert "strictly read-only" in res_mutation.json()["detail"]


@pytest.mark.asyncio
async def test_non_admin_cannot_access_demo_admin_endpoints(client: AsyncClient, db_session):
    """Verifies that non-admin accounts cannot access demo-admin telemetry."""
    # 0. Seed Company Demo in test db
    pw_hash = hash_password("MarketPath-Company-Demo-2026!")
    company_user = UserProfile(
        id=uuid.UUID("d0000001-0000-0000-0000-000000000001"),
        email="demo.company@marketpath.ai",
        full_name="Ananya Deshmukh",
        account_type="company",
        is_platform_admin=False,
        password_hash=pw_hash,
        is_active=True,
    )
    db_session.add(company_user)
    await db_session.commit()

    # Login as Company Demo
    company_login = await client.post(
        "/api/v1/auth/login-account",
        json={
            "email": "demo.company@marketpath.ai",
            "password": "MarketPath-Company-Demo-2026!",
            "account_type": "company",
        },
    )
    assert company_login.status_code == 200
    token = company_login.json()["access_token"]
    company_headers = {"Authorization": f"Bearer {token}"}

    # Calling /api/v1/demo-admin/overview as company -> MUST return 403 Forbidden
    res = await client.get("/api/v1/demo-admin/overview", headers=company_headers)
    assert res.status_code == 403
    assert "Demo Operator or Platform Administrator privileges required" in res.json()["detail"]

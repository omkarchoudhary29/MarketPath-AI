import datetime
import uuid
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.consultation import ConsultationAvailabilityRule, ConsultationRequest
from backend.app.models.user import UserProfile


@pytest.mark.asyncio
async def test_public_consultation_booking_intake(client: AsyncClient, db_session: AsyncSession):
    """Verifies that an unauthenticated public visitor can book a consultation,

    receiving a unique MP-CONS-XXXXXX reference code that is safely stored in the database.
    """
    payload = {
        "full_name": "Ananya Sharma",
        "email": "ananya@auraterra.in",
        "phone": "+91 98200 12345",
        "brand_name": "Aura Terra Living",
        "category": "Home & Decor",
        "business_stage": "Scaling (₹5 Lakh – ₹25 Lakh/mo)",
        "monthly_revenue": "₹5L - ₹25L",
        "challenges": "Need help expanding from Shopify to Amazon and Blinkit without duplicating catalog work.",
        "preferred_date": "2026-11-20",
        "preferred_time_slot": "10:00 AM – 10:30 AM IST",
        "timezone": "Asia/Kolkata",
    }

    # Public POST without any Authorization header
    resp = await client.post("/api/v1/consultations", json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert data["reference_code"].startswith("MP-CONS-")
    assert len(data["reference_code"]) >= 11
    assert data["brand_name"] == "Aura Terra Living"
    assert data["status"] == "submitted"
    assert data["email_delivery_status"] in ["unconfigured_provider", "delivered", "pending"]

    # Verify database persistence
    db_record = await db_session.scalar(
        select(ConsultationRequest).where(ConsultationRequest.reference_code == data["reference_code"])
    )
    assert db_record is not None
    assert db_record.full_name == "Ananya Sharma"
    assert db_record.email == "ananya@auraterra.in"
    assert db_record.status == "submitted"


@pytest.mark.asyncio
async def test_idempotency_key_deduplication(client: AsyncClient, db_session: AsyncSession):
    """Verifies that duplicate submissions with the same idempotency_key return the existing

    consultation record without creating duplicate database rows.
    """
    idempotency_key = f"idem-key-{uuid.uuid4().hex}"
    payload = {
        "full_name": "Vikram Patel",
        "email": "vikram@urbanharvest.in",
        "brand_name": "Urban Harvest Organic",
        "category": "Food & Beverage",
        "business_stage": "Early Stage (< ₹5 Lakh/mo)",
        "preferred_date": "2026-11-20",
        "preferred_time_slot": "11:30 AM – 12:00 PM IST",
        "idempotency_key": idempotency_key,
    }

    resp1 = await client.post("/api/v1/consultations", json=payload)
    assert resp1.status_code == 201
    data1 = resp1.json()

    # Second submission with the exact same idempotency key (simulating double click)
    resp2 = await client.post("/api/v1/consultations", json=payload)
    assert resp2.status_code in [200, 201]
    data2 = resp2.json()

    assert data1["id"] == data2["id"]
    assert data1["reference_code"] == data2["reference_code"]

    # Verify only one database record exists
    records = await db_session.scalars(
        select(ConsultationRequest).where(ConsultationRequest.idempotency_key == idempotency_key)
    )
    assert len(records.all()) == 1


@pytest.mark.asyncio
async def test_dynamic_availability_rules(client: AsyncClient, make_jwt, db_session: AsyncSession):
    """Verifies dynamic availability computation: future dates, past dates, Sundays,

    and platform admin configured blocked dates.
    """
    # 1. Future weekday (guaranteed future date, skipping Sunday)
    future_date = datetime.date.today() + datetime.timedelta(days=7)
    if future_date.weekday() == 6:
        future_date += datetime.timedelta(days=1)
    future_date_str = future_date.isoformat()
    resp = await client.get(f"/api/v1/consultations/availability?date={future_date_str}")
    assert resp.status_code == 200
    avail_data = resp.json()
    assert avail_data["is_available"] is True
    assert len(avail_data["slots"]) >= 5
    assert all(s["available"] is True for s in avail_data["slots"])

    # 2. Past date rejection
    resp_past = await client.get("/api/v1/consultations/availability?date=2026-11-01")
    assert resp_past.status_code == 200
    past_data = resp_past.json()
    assert past_data["is_available"] is False
    assert "past" in past_data["reason"].lower()

    # 3. Sunday rejection (e.g. 2026-11-22 is Sunday)
    resp_sun = await client.get("/api/v1/consultations/availability?date=2026-11-22")
    assert resp_sun.status_code == 200
    sun_data = resp_sun.json()
    assert sun_data["is_available"] is False
    assert "sunday" in sun_data["reason"].lower()

    # 4. Admin creates a blocked date rule for 2026-11-25
    admin_token = make_jwt(user_id=str(uuid.uuid4()), email="admin_ops@marketpath.ai", is_platform_admin=True)
    rule_resp = await client.post(
        "/api/v1/consultations/availability/rules",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "rule_type": "blocked_date",
            "specific_date": "2026-11-25",
            "is_blocked": True,
            "notes": "Annual Platform Infrastructure Maintenance",
        },
    )
    assert rule_resp.status_code == 201

    # Check availability for the newly blocked date
    resp_blocked = await client.get("/api/v1/consultations/availability?date=2026-11-25")
    assert resp_blocked.status_code == 200
    blocked_data = resp_blocked.json()
    assert blocked_data["is_available"] is False
    assert "maintenance" in blocked_data["reason"].lower()


@pytest.mark.asyncio
async def test_slot_capacity_and_double_booking_rejection(client: AsyncClient):
    """Verifies that reserving a slot updates its booked count and rejects concurrent

    or duplicate bookings with HTTP 409 Conflict.
    """
    target_date = "2026-11-19"
    target_slot = "02:00 PM – 02:30 PM IST"

    # 1. Book first reservation for this slot
    payload1 = {
        "full_name": "Rohan Mehra",
        "email": "rohan@zephyrtea.com",
        "brand_name": "Zephyr Artisanal Tea",
        "category": "Food & Beverage",
        "business_stage": "Scaling (₹5 Lakh – ₹25 Lakh/mo)",
        "preferred_date": target_date,
        "preferred_time_slot": target_slot,
    }
    resp1 = await client.post("/api/v1/consultations", json=payload1)
    assert resp1.status_code == 201

    # 2. Check availability: the booked slot must now show available=False
    avail_resp = await client.get(f"/api/v1/consultations/availability?date={target_date}")
    assert avail_resp.status_code == 200
    avail_data = avail_resp.json()
    booked_slot_info = next((s for s in avail_data["slots"] if s["slot"] == target_slot), None)
    assert booked_slot_info is not None
    assert booked_slot_info["available"] is False
    assert booked_slot_info["booked_count"] == 1

    # 3. Second customer attempts to book the same reserved slot -> must be rejected with HTTP 409
    payload2 = {
        "full_name": "Kavita Rao",
        "email": "kavita@botanicalglow.in",
        "brand_name": "Botanical Glow",
        "category": "Beauty & Personal Care",
        "business_stage": "Early Stage (< ₹5 Lakh/mo)",
        "preferred_date": target_date,
        "preferred_time_slot": target_slot,
    }
    resp2 = await client.post("/api/v1/consultations", json=payload2)
    assert resp2.status_code == 409
    err = resp2.json()
    assert "already reserved" in err["detail"].lower()


@pytest.mark.asyncio
async def test_zero_rollback_email_failure_safety(client: AsyncClient, db_session: AsyncSession):
    """STRICT ZERO-ROLLBACK GUARANTEE:

    Verifies that if transactional email dispatch raises an unhandled exception
    (network timeout / SMTP crash), the booking is NEVER rolled back or deleted.
    It remains committed in the database with status="submitted" and
    email_delivery_status="failed".
    """
    payload = {
        "full_name": "Neha Gupta",
        "email": "neha@vediccure.in",
        "brand_name": "Vedic Cure Herbals",
        "category": "Health & Wellness",
        "business_stage": "Scaling (₹5 Lakh – ₹25 Lakh/mo)",
        "preferred_date": "2026-11-20",
        "preferred_time_slot": "03:30 PM – 04:00 PM IST",
    }

    # Simulate catastrophic SMTP failure during email dispatch
    with patch(
        "backend.app.services.email_service.EmailService.send_consultation_confirmation_email",
        side_effect=Exception("SMTP Connection Reset by Peer [WinError 10054]"),
    ):
        resp = await client.post("/api/v1/consultations", json=payload)
        # Booking still succeeds!
        assert resp.status_code == 201
        data = resp.json()
        assert data["reference_code"].startswith("MP-CONS-")
        assert data["email_delivery_status"] == "failed"

    # Verify that the booking is safely stored in the database despite email crash
    db_record = await db_session.scalar(
        select(ConsultationRequest).where(ConsultationRequest.reference_code == data["reference_code"])
    )
    assert db_record is not None
    assert db_record.brand_name == "Vedic Cure Herbals"
    assert db_record.status == "submitted"
    assert db_record.email_delivery_status == "failed"


@pytest.mark.asyncio
async def test_admin_consultations_management(client: AsyncClient, make_jwt, db_session: AsyncSession):
    """Verifies that platform administrators can list, search, filter, and assign consultations."""
    # 1. Create a consultation
    consultation = ConsultationRequest(
        reference_code="MP-CONS-TESTADM",
        full_name="Rajesh Sen",
        email="rajesh@senleather.com",
        brand_name="Sen & Co Handcrafted Leather",
        category="Footwear & Leather",
        business_stage="Mature (> ₹1 Crore/mo)",
        preferred_date=datetime.date(2026, 11, 24),
        preferred_time_slot="10:00 AM – 10:30 AM IST",
        status="submitted",
    )
    db_session.add(consultation)
    await db_session.commit()
    await db_session.refresh(consultation)

    # 2. Admin retrieves consultation list
    admin_token = make_jwt(user_id=str(uuid.uuid4()), email="ops_lead@marketpath.ai", is_platform_admin=True)
    list_resp = await client.get(
        "/api/v1/admin/consultations",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert "stats" in list_data
    assert list_data["stats"]["total_consultations"] >= 1
    assert any(c["reference_code"] == "MP-CONS-TESTADM" for c in list_data["consultations"])

    # 3. Admin assigns consultant
    consultant_id = str(uuid.uuid4())
    assign_resp = await client.post(
        f"/api/v1/consultations/{consultation.id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "consultant_id": consultant_id,
            "consultant_name": "Priya Kapoor (Senior Omnichannel Strategist)",
        },
    )
    assert assign_resp.status_code == 200
    assigned_data = assign_resp.json()
    assert assigned_data["status"] == "assigned"
    assert assigned_data["assigned_consultant_name"] == "Priya Kapoor (Senior Omnichannel Strategist)"


@pytest.mark.asyncio
async def test_consultant_isolation_and_workflow(client: AsyncClient, make_jwt, db_session: AsyncSession):
    """Verifies consultant workspace isolation and end-to-end workflow:

    - Consultant A can view assigned consultation and confirm/report.
    - Consultant B receives 403 Forbidden when attempting to modify Consultant A's booking.
    - Diagnostic report filed has internal_notes, but client-facing endpoint strictly redacts it.
    """
    consultant_a_id = uuid.uuid4()
    consultant_b_id = uuid.uuid4()

    # Create user profile for Consultant A
    user_a = UserProfile(
        id=consultant_a_id,
        email="consultant_a@marketpath.ai",
        full_name="Consultant A",
        role="consultant",
        is_platform_admin=False,
    )
    # Create user profile for Consultant B
    user_b = UserProfile(
        id=consultant_b_id,
        email="consultant_b@marketpath.ai",
        full_name="Consultant B",
        role="consultant",
        is_platform_admin=False,
    )
    db_session.add_all([user_a, user_b])

    # Create consultation assigned to Consultant A
    consultation = ConsultationRequest(
        reference_code="MP-CONS-ISOLAT",
        full_name="Sunil Dutt",
        email="sunil@duttceramics.in",
        brand_name="Dutt Ceramics",
        category="Home & Decor",
        business_stage="Scaling (₹5 Lakh – ₹25 Lakh/mo)",
        status="assigned",
        assigned_consultant_id=consultant_a_id,
        assigned_consultant_name="Consultant A",
        preferred_date=datetime.date(2026, 11, 21),
        preferred_time_slot="11:30 AM – 12:00 PM IST",
    )
    db_session.add(consultation)
    await db_session.commit()
    await db_session.refresh(consultation)

    token_a = make_jwt(user_id=str(consultant_a_id), email="consultant_a@marketpath.ai")
    token_b = make_jwt(user_id=str(consultant_b_id), email="consultant_b@marketpath.ai")

    # 1. Consultant A checks assigned consultations: sees Dutt Ceramics
    resp_a_list = await client.get(
        "/api/v1/consultations/assigned",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a_list.status_code == 200
    a_items = resp_a_list.json()
    assert any(c["id"] == str(consultation.id) for c in a_items)

    # 2. Consultant B checks assigned consultations: does NOT see Dutt Ceramics
    resp_b_list = await client.get(
        "/api/v1/consultations/assigned",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b_list.status_code == 200
    b_items = resp_b_list.json()
    assert not any(c["id"] == str(consultation.id) for c in b_items)

    # 3. Consultant B attempts to confirm Consultant A's booking: MUST be rejected with HTTP 403 Forbidden
    resp_b_confirm = await client.post(
        f"/api/v1/consultations/{consultation.id}/confirm",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "scheduled_at": "2026-11-21T11:30:00Z",
            "meeting_link": "https://meet.marketpath.ai/rogue-link",
        },
    )
    assert resp_b_confirm.status_code == 403

    # 4. Consultant A confirms the appointment
    resp_a_confirm = await client.post(
        f"/api/v1/consultations/{consultation.id}/confirm",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "scheduled_at": "2026-11-21T11:30:00Z",
            "meeting_link": "https://meet.marketpath.ai/consult-mp-cons-isolat",
            "duration_minutes": 30,
        },
    )
    assert resp_a_confirm.status_code == 200
    assert resp_a_confirm.json()["status"] == "confirmed"

    # 5. Consultant A files diagnostic report
    report_payload = {
        "report_summary": "Dutt Ceramics has strong handcrafted catalog depth. Recommended transition to 3-ply corrugated master packaging to eliminate Amazon transit breakage.",
        "recommendations": [
            "Enroll in Amazon Launchpad program",
            "Enable Zepto regional dark-store stocking for top 5 terracotta planters",
        ],
        "action_items": [
            "Merchant to provide GS1 barcode certificates",
            "Advisor to send packaging testing specs",
        ],
        "internal_notes": "CONFIDENTIAL: Merchant margins are tight (18% net). Recommend against high-take-rate influencer agencies.",
    }
    resp_a_report = await client.post(
        f"/api/v1/consultations/{consultation.id}/report",
        headers={"Authorization": f"Bearer {token_a}"},
        json=report_payload,
    )
    assert resp_a_report.status_code == 200
    assert resp_a_report.json()["status"] == "completed"

    # 6. Public/Client accesses report: verify strict redaction of internal_notes
    resp_client_report = await client.get(f"/api/v1/consultations/{consultation.id}/report")
    assert resp_client_report.status_code == 200
    client_report = resp_client_report.json()
    assert "Dutt Ceramics" in client_report["brand_name"]
    assert len(client_report["recommendations"]) == 2
    # Verify internal_notes is not in the client-facing response schema
    assert "internal_notes" not in client_report

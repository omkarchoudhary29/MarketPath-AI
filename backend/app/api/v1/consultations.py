import datetime
import logging
import secrets
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.calendar import BusinessCalendarEvent
from backend.app.models.consultation import ConsultationAvailabilityRule, ConsultationRequest
from backend.app.models.notification import Notification, NotificationOutbox
from backend.app.models.organization import OrganizationMember
from backend.app.models.user import UserProfile
from backend.app.schemas.consultation import (
    ConsultationAdminStats,
    ConsultationAssign,
    ConsultationAvailabilityResponse,
    ConsultationAvailabilityRuleCreate,
    ConsultationAvailabilityRuleResponse,
    ConsultationCancel,
    ConsultationConfirm,
    ConsultationCreate,
    ConsultationReportRead,
    ConsultationReportSubmit,
    ConsultationReschedule,
    ConsultationResponse,
    ConsultationSlotInfo,
    ConsultationUpdate,
)
from backend.app.services.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consultations", tags=["Consultations"])

# Standard Advisory Slots for MarketPath AI (Asia/Kolkata)
STANDARD_SLOTS = [
    "10:00 AM – 10:30 AM IST",
    "11:30 AM – 12:00 PM IST",
    "02:00 PM – 02:30 PM IST",
    "03:30 PM – 04:00 PM IST",
    "05:00 PM – 05:30 PM IST",
]

# Slot start times in 24-hr format (hours, minutes) for today cutoff check
SLOT_START_TIMES = {
    "10:00 AM – 10:30 AM IST": (10, 0),
    "11:30 AM – 12:00 PM IST": (11, 30),
    "02:00 PM – 02:30 PM IST": (14, 0),
    "03:30 PM – 04:00 PM IST": (15, 30),
    "05:00 PM – 05:30 PM IST": (17, 0),
}

IST_OFFSET = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def _get_current_ist_datetime() -> datetime.datetime:
    """Returns the current datetime in Asia/Kolkata timezone."""
    return datetime.datetime.now(IST_OFFSET)


def _generate_reference_code() -> str:
    """Generates a human-friendly consultation booking reference code."""
    return f"MP-CONS-{secrets.token_hex(3).upper()}"


# ==============================================================================
# PUBLIC AVAILABILITY & BOOKING ENDPOINTS
# ==============================================================================

@router.get("/availability", response_model=ConsultationAvailabilityResponse)
async def check_availability(
    date: datetime.date = Query(..., description="Target booking date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """Dynamic availability engine with working hours, slot capacity, and blocked date checks."""
    now_ist = _get_current_ist_datetime()
    today_ist = now_ist.date()

    # Reject past dates in Asia/Kolkata
    if date < today_ist:
        return ConsultationAvailabilityResponse(
            date=date,
            timezone="Asia/Kolkata",
            is_available=False,
            reason="Cannot book consultations for dates in the past.",
            slots=[],
        )

    # Sunday check (weekday == 6): Default blocked unless explicit unblock rule
    is_sunday = date.weekday() == 6

    # Query custom rules for this specific date
    rules_res = await db.execute(
        select(ConsultationAvailabilityRule).where(
            or_(
                ConsultationAvailabilityRule.specific_date == date,
                ConsultationAvailabilityRule.day_of_week == date.weekday(),
            )
        )
    )
    rules = rules_res.scalars().all()

    # Determine if blocked by date-specific or recurring rule
    date_rule = next((r for r in rules if r.specific_date == date), None)
    dow_rule = next((r for r in rules if r.day_of_week == date.weekday() and not r.specific_date), None)

    if date_rule and bool(date_rule.is_blocked):
        return ConsultationAvailabilityResponse(
            date=date,
            timezone="Asia/Kolkata",
            is_available=False,
            reason=date_rule.notes or "This date is unavailable for consultation bookings.",
            slots=[],
        )

    if is_sunday and (not date_rule or bool(date_rule.is_blocked)):
        return ConsultationAvailabilityResponse(
            date=date,
            timezone="Asia/Kolkata",
            is_available=False,
            reason="Sunday is a non-working day for advisory sessions.",
            slots=[],
        )

    # Default capacity is 1 per slot (or overridden by rule)
    default_capacity = 1
    if date_rule and date_rule.slot_capacity:
        default_capacity = date_rule.slot_capacity
    elif dow_rule and dow_rule.slot_capacity:
        default_capacity = dow_rule.slot_capacity

    # Query existing active bookings for this date
    existing_bookings_res = await db.execute(
        select(ConsultationRequest).where(
            ConsultationRequest.preferred_date == date,
            ConsultationRequest.status.not_in(["cancelled", "no_show"]),
        )
    )
    existing_bookings = existing_bookings_res.scalars().all()

    # Count bookings per slot
    booked_counts = {}
    for booking in existing_bookings:
        slot = booking.preferred_time_slot
        if slot:
            # Normalize slot string
            norm_slot = slot.replace("-", "–").strip()
            booked_counts[norm_slot] = booked_counts.get(norm_slot, 0) + 1

    slot_infos: List[ConsultationSlotInfo] = []
    for slot_name in STANDARD_SLOTS:
        # Check current booked count
        count = booked_counts.get(slot_name, 0)
        # Check fallback with plain hyphen
        hyphen_variant = slot_name.replace("–", "-")
        count += booked_counts.get(hyphen_variant, 0)

        is_avail = count < default_capacity

        # If date is today, check if slot start time has already passed
        if date == today_ist and slot_name in SLOT_START_TIMES:
            start_h, start_m = SLOT_START_TIMES[slot_name]
            slot_time = now_ist.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
            if now_ist >= slot_time:
                is_avail = False

        slot_infos.append(
            ConsultationSlotInfo(
                slot=slot_name,
                available=is_avail,
                capacity=default_capacity,
                booked_count=count,
            )
        )

    overall_available = any(s.available for s in slot_infos)

    return ConsultationAvailabilityResponse(
        date=date,
        timezone="Asia/Kolkata",
        is_available=overall_available,
        reason=None if overall_available else "All advisory slots for this date are fully reserved.",
        slots=slot_infos,
    )


@router.post("", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def submit_consultation(
    payload: ConsultationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Public intake for growth consultations with idempotency, double-booking guard, and zero-rollback email."""
    # 1. Idempotency Check: prevent double-clicks
    if payload.idempotency_key:
        existing_idempotent = await db.scalar(
            select(ConsultationRequest).where(ConsultationRequest.idempotency_key == payload.idempotency_key)
        )
        if existing_idempotent:
            logger.info(f"Idempotent consultation request detected for key {payload.idempotency_key}.")
            return existing_idempotent

    # 2. Date and Time Slot Validation
    if payload.preferred_date:
        now_ist = _get_current_ist_datetime()
        today_ist = now_ist.date()

        if payload.preferred_date < today_ist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Consultations cannot be scheduled for dates in the past.",
            )

        # Check blocked date rules
        blocked_rule = await db.scalar(
            select(ConsultationAvailabilityRule).where(
                ConsultationAvailabilityRule.specific_date == payload.preferred_date,
                ConsultationAvailabilityRule.is_blocked == 1,
            )
        )
        if blocked_rule:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=blocked_rule.notes or f"The date {payload.preferred_date} is not available for bookings.",
            )

        # Check Sunday
        if payload.preferred_date.weekday() == 6 and not blocked_rule:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Sunday is a non-working day for advisory sessions.",
            )

        # Check Slot Capacity
        if payload.preferred_time_slot:
            # Normalize slot string
            norm_slot = payload.preferred_time_slot.replace("-", "–").strip()
            hyphen_slot = payload.preferred_time_slot.replace("–", "-").strip()

            active_bookings_count = await db.scalar(
                select(func.count(ConsultationRequest.id)).where(
                    ConsultationRequest.preferred_date == payload.preferred_date,
                    or_(
                        ConsultationRequest.preferred_time_slot == norm_slot,
                        ConsultationRequest.preferred_time_slot == hyphen_slot,
                    ),
                    ConsultationRequest.status.not_in(["cancelled", "no_show"]),
                )
            )

            # Slot capacity (default 1)
            capacity = 1
            if active_bookings_count and active_bookings_count >= capacity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"The time slot '{payload.preferred_time_slot}' on {payload.preferred_date} is already reserved. Please select an alternate slot.",
                )

    # 3. Generate Unique Non-Sequential Reference Code
    ref_code = _generate_reference_code()
    for _ in range(5):
        existing_ref = await db.scalar(
            select(ConsultationRequest.id).where(ConsultationRequest.reference_code == ref_code)
        )
        if not existing_ref:
            break
        ref_code = _generate_reference_code()

    # 4. ZERO-ROLLBACK GUARANTEE: Persist booking to Database FIRST
    consultation = ConsultationRequest(
        reference_code=ref_code,
        full_name=payload.full_name,
        email=str(payload.email),
        phone=payload.phone,
        brand_name=payload.brand_name,
        category=payload.category,
        business_stage=payload.business_stage,
        monthly_revenue=payload.monthly_revenue,
        challenges=payload.challenges,
        preferred_date=payload.preferred_date,
        preferred_time_slot=payload.preferred_time_slot,
        timezone=payload.timezone,
        status="submitted",
        email_delivery_status="pending",
        idempotency_key=payload.idempotency_key,
    )
    db.add(consultation)
    await db.commit()
    await db.refresh(consultation)

    # 5. Decoupled Transactional Email Notifications
    # If email service fails or is unconfigured, the consultation booking remains 100% saved in the database
    email_delivery_status = "unconfigured_provider"
    try:
        # Customer acknowledgement email
        customer_email = EmailService.send_consultation_confirmation_email(
            to_email=str(payload.email),
            full_name=payload.full_name,
            brand_name=payload.brand_name,
            reference_code=ref_code,
            preferred_date=str(payload.preferred_date) if payload.preferred_date else None,
            time_slot=payload.preferred_time_slot,
            timezone=payload.timezone,
            status="submitted",
        )
        email_delivery_status = customer_email.get("status", "unconfigured_provider")

        # Internal notification to advisory team
        EmailService.send_internal_consultation_alert(
            reference_code=ref_code,
            full_name=payload.full_name,
            email=str(payload.email),
            phone=payload.phone,
            brand_name=payload.brand_name,
            category=payload.category,
            business_stage=payload.business_stage,
            monthly_revenue=payload.monthly_revenue,
            preferred_date=str(payload.preferred_date) if payload.preferred_date else None,
            time_slot=payload.preferred_time_slot,
            challenges=payload.challenges,
        )
    except Exception as ex:
        logger.warning(f"Decoupled email notification dispatch encountered an error: {ex}")
        email_delivery_status = "failed"

    # Update delivery status safely and record outbox entry
    try:
        consultation.email_delivery_status = email_delivery_status
        outbox = NotificationOutbox(
            recipient_email=str(payload.email),
            recipient_name=payload.full_name,
            notification_type="consultation_acknowledgement",
            subject=f"MarketPath AI — Consultation Request Received [{ref_code}]",
            context_data={"reference_code": ref_code, "brand_name": payload.brand_name},
            status="accepted_by_provider" if email_delivery_status == "sent" else ("pending" if email_delivery_status == "unconfigured_provider" else "failed"),
            attempts_count=1 if email_delivery_status in ("sent", "delivered") else 0,
            last_attempt_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(outbox)
        await db.commit()
        await db.refresh(consultation)
    except Exception as commit_err:
        logger.error(f"Failed to update email delivery status on consultation {ref_code}: {commit_err}")

    return consultation


# ==============================================================================
# OPERATOR & CONSULTANT MANAGEMENT ENDPOINTS
# ==============================================================================

@router.get("/stats", response_model=ConsultationAdminStats)
async def get_consultation_stats(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated consultation metrics for Admin and Consultant portals."""
    query = select(ConsultationRequest)
    if current_user.role == "consultant":
        query = query.where(ConsultationRequest.assigned_consultant_id == current_user.id)

    res = await db.execute(query)
    consultations = res.scalars().all()

    total = len(consultations)
    breakdown = {}
    submitted = 0
    confirmed = 0
    completed = 0
    cancelled = 0

    for c in consultations:
        st = c.status
        breakdown[st] = breakdown.get(st, 0) + 1
        if st == "submitted":
            submitted += 1
        elif st in ["confirmed", "scheduled"]:
            confirmed += 1
        elif st == "completed":
            completed += 1
        elif st == "cancelled":
            cancelled += 1

    return ConsultationAdminStats(
        total_consultations=total,
        submitted_count=submitted,
        confirmed_count=confirmed,
        completed_count=completed,
        cancelled_count=cancelled,
        status_breakdown=breakdown,
    )


@router.get("", response_model=List[ConsultationResponse])
async def list_consultations(
    status_filter: Optional[str] = Query(None, alias="status"),
    consultant_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Operator / Consultant endpoint to view consultation requests with search and filters."""
    query = select(ConsultationRequest).order_by(ConsultationRequest.created_at.desc())

    # Consultants can only see their assigned consultations unless role is admin
    if current_user.role == "consultant":
        query = query.where(ConsultationRequest.assigned_consultant_id == current_user.id)
    elif consultant_id:
        query = query.where(ConsultationRequest.assigned_consultant_id == consultant_id)

    if status_filter:
        query = query.where(ConsultationRequest.status == status_filter)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                ConsultationRequest.reference_code.ilike(search_term),
                ConsultationRequest.brand_name.ilike(search_term),
                ConsultationRequest.full_name.ilike(search_term),
                ConsultationRequest.email.ilike(search_term),
            )
        )

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/assigned", response_model=List[ConsultationResponse])
async def list_assigned_consultations(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns consultations assigned to the authenticated consultant (strict tenant isolation)."""
    query = (
        select(ConsultationRequest)
        .where(ConsultationRequest.assigned_consultant_id == current_user.id)
        .order_by(ConsultationRequest.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{consultation_id}/assign", response_model=ConsultationResponse)
async def assign_consultant(
    consultation_id: uuid.UUID,
    payload: ConsultationAssign,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Platform Admin assigns an internal category specialist or growth consultant."""
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can assign consultants.",
        )

    stmt = select(ConsultationRequest).where(ConsultationRequest.id == consultation_id)
    consultation = await db.scalar(stmt)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation request not found")

    consultation.assigned_consultant_id = payload.consultant_id
    consultation.assigned_consultant_name = payload.consultant_name
    consultation.status = "assigned"

    await db.commit()
    await db.refresh(consultation)
    return consultation


@router.post("/{consultation_id}/confirm", response_model=ConsultationResponse)
async def confirm_consultation(
    consultation_id: uuid.UUID,
    payload: ConsultationConfirm,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirms appointment schedule, creates calendar event, and generates meeting link."""
    stmt = select(ConsultationRequest).where(ConsultationRequest.id == consultation_id)
    consultation = await db.scalar(stmt)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation request not found")

    # Consultant isolation check
    if current_user.role == "consultant" and consultation.assigned_consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only permitted to confirm consultations assigned to your profile.",
        )

    meeting_link = payload.meeting_link or f"https://meet.marketpath.ai/consult-{consultation.reference_code.lower()}"
    consultation.scheduled_at = payload.scheduled_at
    consultation.duration_minutes = payload.duration_minutes
    consultation.meeting_link = meeting_link
    consultation.status = "confirmed"

    # If the user or brand has an organization in the platform, create a BusinessCalendarEvent
    user_res = await db.execute(select(UserProfile).where(UserProfile.email == consultation.email))
    matched_user = user_res.scalar_one_or_none()
    if matched_user:
        org_member_res = await db.execute(
            select(OrganizationMember).where(OrganizationMember.user_id == matched_user.id)
        )
        membership = org_member_res.scalars().first()
        if membership:
            cal_event = BusinessCalendarEvent(
                organization_id=membership.organization_id,
                user_id=matched_user.id,
                event_type="consultation",
                title=f"Growth Consultation: {consultation.brand_name}",
                description=f"Diagnostic consultation with {consultation.assigned_consultant_name or 'MarketPath Specialist'}. Meeting: {meeting_link}",
                start_time=payload.scheduled_at,
                end_time=payload.scheduled_at + datetime.timedelta(minutes=payload.duration_minutes),
                color="#0D9488",
                is_all_day=False,
                status="scheduled",
            )
            db.add(cal_event)

            # In-app notification
            db.add(
                Notification(
                    organization_id=membership.organization_id,
                    user_id=matched_user.id,
                    domain="business",
                    title="Growth Consultation Confirmed",
                    message=f"Your consultation for {consultation.brand_name} is confirmed for {payload.scheduled_at.strftime('%d %b %Y, %I:%M %p')}.",
                    notification_type="success",
                    severity="info",
                    link="/app/calendar",
                )
            )

    await db.commit()
    await db.refresh(consultation)

    # Dispatch confirmation email to client
    try:
        EmailService.send_consultation_confirmation_email(
            to_email=consultation.email,
            full_name=consultation.full_name,
            brand_name=consultation.brand_name,
            reference_code=consultation.reference_code,
            preferred_date=payload.scheduled_at.strftime("%Y-%m-%d"),
            time_slot=payload.scheduled_at.strftime("%I:%M %p"),
            timezone=consultation.timezone,
            status="confirmed",
        )
    except Exception as ex:
        logger.warning(f"Failed to dispatch appointment confirmation email: {ex}")

    return consultation


@router.post("/{consultation_id}/reschedule", response_model=ConsultationResponse)
async def reschedule_consultation(
    consultation_id: uuid.UUID,
    payload: ConsultationReschedule,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reschedules an appointment with recorded reason and updated date/time slot."""
    stmt = select(ConsultationRequest).where(ConsultationRequest.id == consultation_id)
    consultation = await db.scalar(stmt)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation request not found")

    # Consultant isolation check
    if current_user.role == "consultant" and consultation.assigned_consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only permitted to reschedule consultations assigned to your profile.",
        )

    consultation.preferred_date = payload.preferred_date
    consultation.preferred_time_slot = payload.preferred_time_slot
    consultation.status = "rescheduled"
    if payload.reason:
        existing_notes = consultation.notes or ""
        consultation.notes = f"{existing_notes}\n[Rescheduled by {current_user.email}]: {payload.reason}".strip()

    await db.commit()
    await db.refresh(consultation)
    return consultation


@router.post("/{consultation_id}/cancel", response_model=ConsultationResponse)
async def cancel_consultation(
    consultation_id: uuid.UUID,
    payload: ConsultationCancel,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancels a consultation booking with a required recorded cancellation reason."""
    stmt = select(ConsultationRequest).where(ConsultationRequest.id == consultation_id)
    consultation = await db.scalar(stmt)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation request not found")

    # Consultant isolation check
    if current_user.role == "consultant" and consultation.assigned_consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only permitted to cancel consultations assigned to your profile.",
        )

    consultation.status = "cancelled"
    consultation.cancellation_reason = payload.reason

    await db.commit()
    await db.refresh(consultation)
    return consultation


@router.post("/{consultation_id}/report", response_model=ConsultationResponse)
async def submit_consultation_report(
    consultation_id: uuid.UUID,
    payload: ConsultationReportSubmit,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Consultant files diagnostic observations, recommendations, and action plan."""
    stmt = select(ConsultationRequest).where(ConsultationRequest.id == consultation_id)
    consultation = await db.scalar(stmt)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation request not found")

    # Consultant isolation check
    if current_user.role == "consultant" and consultation.assigned_consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only permitted to submit reports for consultations assigned to your profile.",
        )

    consultation.internal_notes = payload.internal_notes
    consultation.report_summary = payload.report_summary
    consultation.recommendations = payload.recommendations
    consultation.action_items = payload.action_items
    consultation.status = "completed"

    await db.commit()
    await db.refresh(consultation)
    return consultation


@router.get("/{consultation_id}/report", response_model=ConsultationReportRead)
async def get_consultation_report(
    consultation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves client-facing consultation report (strictly redacting private internal notes)."""
    stmt = select(ConsultationRequest).where(ConsultationRequest.id == consultation_id)
    consultation = await db.scalar(stmt)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation report not found")
    if consultation.status != "completed" or not consultation.report_summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultation report has not yet been filed for this booking.",
        )

    return ConsultationReportRead.model_validate(consultation)


@router.patch("/{consultation_id}", response_model=ConsultationResponse)
async def update_consultation_status(
    consultation_id: uuid.UUID,
    payload: ConsultationUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update status, notes, or meeting link for a consultation booking."""
    stmt = select(ConsultationRequest).where(ConsultationRequest.id == consultation_id)
    consultation = await db.scalar(stmt)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation request not found")

    if current_user.role == "consultant" and consultation.assigned_consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only permitted to update consultations assigned to your profile.",
        )

    if payload.status is not None:
        consultation.status = payload.status
    if payload.notes is not None:
        consultation.notes = payload.notes
    if payload.internal_notes is not None:
        consultation.internal_notes = payload.internal_notes
    if payload.meeting_link is not None:
        consultation.meeting_link = payload.meeting_link

    await db.commit()
    await db.refresh(consultation)
    return consultation


# ==============================================================================
# AVAILABILITY RULES (ADMIN MANAGEMENT)
# ==============================================================================

@router.get("/availability/rules", response_model=List[ConsultationAvailabilityRuleResponse])
async def list_availability_rules(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists configured availability rules and blocked dates."""
    res = await db.execute(
        select(ConsultationAvailabilityRule).order_by(ConsultationAvailabilityRule.created_at.desc())
    )
    return res.scalars().all()


@router.post("/availability/rules", response_model=ConsultationAvailabilityRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_availability_rule(
    payload: ConsultationAvailabilityRuleCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Platform Admin creates a blocked date, holiday, or capacity override rule."""
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can configure availability rules.",
        )

    rule = ConsultationAvailabilityRule(
        rule_type=payload.rule_type,
        specific_date=payload.specific_date,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
        slot_capacity=payload.slot_capacity,
        is_blocked=1 if payload.is_blocked else 0,
        notes=payload.notes,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/availability/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability_rule(
    rule_id: uuid.UUID,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Platform Admin deletes an availability rule."""
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can delete availability rules.",
        )

    rule = await db.scalar(
        select(ConsultationAvailabilityRule).where(ConsultationAvailabilityRule.id == rule_id)
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Availability rule not found")

    await db.delete(rule)
    await db.commit()
    return None

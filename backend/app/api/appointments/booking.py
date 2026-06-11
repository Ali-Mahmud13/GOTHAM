from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_session
from app.core.security import get_current_user_compat
from app.models.auth import AuthUser
from app.models.appointments import Appointment, RegistrationRequest
from app.models.patient import Patient

from .schemas import (
    AppointmentOut, BookingRequest, TimeSlotOut, RescheduleRequest
)
from .utils import (
    _require_patient, _parse_hhmm, _is_past, _is_within_lead_time,
    _validate_slot_against_availability,
    _appointment_out, _effective_windows_for_date, _generate_slots,
    BOOKING_HORIZON_DAYS, MIN_BOOKING_LEAD_HOURS
)

router = APIRouter()

@router.get("/doctors/{doctor_id}/slots", response_model=List[TimeSlotOut])
def get_available_slots(
    doctor_id: int,
    date: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Return bookable time slots for a doctor on a specific date."""
    target_date_str = date
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if target_date < datetime.today().date():
        return []

    wins = _effective_windows_for_date(session, doctor_id, target_date_str)
    if wins is None or not wins:
        return []

    all_slots = []
    for st, en, dur in wins:
        all_slots.extend(_generate_slots(st, en, dur))

    booked = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == doctor_id)
        .where(Appointment.appointment_date == target_date_str)
        .where(Appointment.status.in_(["booked", "pending_approval"]))
    ).all()
    booked_starts = {b.start_time for b in booked}

    return [
        TimeSlotOut(start_time=s, end_time=e, available=(s not in booked_starts))
        for s, e in all_slots
    ]


@router.post("/book", response_model=AppointmentOut, status_code=201)
def book_appointment(
    request: BookingRequest,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Book an appointment for the authenticated patient."""
    _require_patient(user)

    # Verify the target doctor exists and is verified
    doctor = session.get(AuthUser, request.doctor_id)
    if not doctor or doctor.role != "doctor" or not doctor.is_active or doctor.verification_status != "verified":
        raise HTTPException(status_code=404, detail="Doctor not found or not accepting appointments.")

    # Validate slot
    _validate_slot_against_availability(
        session, request.doctor_id, request.appointment_date, request.start_time, request.end_time
    )

    if _is_past(request.appointment_date, request.start_time, request.timezone):
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past.")

    if _is_within_lead_time(request.appointment_date, request.start_time, request.timezone):
        raise HTTPException(
            status_code=400,
            detail=f"Appointments must be booked at least {MIN_BOOKING_LEAD_HOURS} hour(s) in advance.",
        )

    # Pre-check for conflicts
    existing = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == request.doctor_id)
        .where(Appointment.appointment_date == request.appointment_date)
        .where(Appointment.start_time == request.start_time)
        .where(Appointment.status.in_(["booked", "pending_approval"]))
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Time slot not available.")

    patient_record = session.get(Patient, user.patient_id) if user.patient_id else None
    registered_doctor_id = patient_record.doctor_id if patient_record else None
    is_different_doctor = registered_doctor_id != request.doctor_id
    wants_registration = request.request_registration and is_different_doctor

    appt_status = "pending_approval" if wants_registration else "booked"

    appointment = Appointment(
        doctor_id=request.doctor_id,
        patient_id=user.id,
        appointment_date=request.appointment_date,
        start_time=request.start_time,
        end_time=request.end_time,
        timezone=request.timezone,
        status=appt_status,
        notes=request.notes,
    )
    session.add(appointment)
    session.flush()

    if wants_registration:
        reg_request = RegistrationRequest(
            patient_id=user.id,
            doctor_id=request.doctor_id,
            appointment_id=appointment.id,
            status="pending",
        )
        session.add(reg_request)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Slot just got booked.")
    
    session.refresh(appointment)
    return _appointment_out(appointment, session)


@router.get("/my", response_model=List[AppointmentOut])
def get_my_appointments(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return all appointments for the authenticated user."""
    if user.role == "doctor":
        appts = session.exec(
            select(Appointment)
            .where(Appointment.doctor_id == user.id)
            .where(Appointment.status.in_(["booked", "completed", "pending_approval"]))
            .order_by(Appointment.appointment_date, Appointment.start_time)
        ).all()
    else:
        appts = session.exec(
            select(Appointment)
            .where(Appointment.patient_id == user.id)
            .where(Appointment.status.in_(["booked", "completed", "pending_approval"]))
            .order_by(Appointment.appointment_date, Appointment.start_time)
        ).all()

    return [_appointment_out(a, session) for a in appts]


@router.put("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: int,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Cancel an appointment."""
    appt = session.get(Appointment, appointment_id)
    if not appt or (appt.doctor_id != user.id and appt.patient_id != user.id):
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appt.status not in ("booked", "pending_approval"):
        raise HTTPException(status_code=400, detail="Cannot cancel.")

    appt.status = "cancelled"
    appt.cancelled_by = "doctor" if user.id == appt.doctor_id else "patient"
    appt.updated_at = datetime.utcnow()
    session.add(appt)
    session.commit()
    session.refresh(appt)
    return _appointment_out(appt, session)


@router.put("/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule_appointment(
    appointment_id: int,
    request: RescheduleRequest,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Reschedule an appointment."""
    appt = session.get(Appointment, appointment_id)
    if not appt or (appt.doctor_id != user.id and appt.patient_id != user.id):
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appt.status not in ("booked", "pending_approval"):
        raise HTTPException(status_code=400, detail="Cannot reschedule.")

    _validate_slot_against_availability(
        session, appt.doctor_id, request.appointment_date, request.start_time, request.end_time
    )

    if _is_past(request.appointment_date, request.start_time, request.timezone):
        raise HTTPException(status_code=400, detail="Cannot reschedule to a past time.")

    if _is_within_lead_time(request.appointment_date, request.start_time, request.timezone):
        raise HTTPException(
            status_code=400,
            detail=f"Rescheduled slot must be at least {MIN_BOOKING_LEAD_HOURS} hour(s) from now.",
        )

    # Prevent double-booking the new slot
    conflict = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == appt.doctor_id)
        .where(Appointment.appointment_date == request.appointment_date)
        .where(Appointment.start_time == request.start_time)
        .where(Appointment.status.in_(["booked", "pending_approval"]))
        .where(Appointment.id != appt.id)
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail="That slot is already booked.")

    appt.appointment_date = request.appointment_date
    appt.start_time = request.start_time
    appt.end_time = request.end_time
    appt.timezone = request.timezone
    appt.rescheduled_by = "doctor" if user.id == appt.doctor_id else "patient"
    appt.updated_at = datetime.utcnow()
    session.add(appt)
    session.commit()
    session.refresh(appt)
    return _appointment_out(appt, session)


@router.get("/upcoming", response_model=List[AppointmentOut])
def get_upcoming_appointments(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
    limit: int = 5,
):
    """Return upcoming appointments for the authenticated user."""
    today = date.today().isoformat()
    now_time = datetime.now().strftime("%H:%M")

    if user.role == "doctor":
        appts = session.exec(
            select(Appointment)
            .where(Appointment.doctor_id == user.id)
            .where(Appointment.status.in_(["booked", "pending_approval"]))
            .where(
                (Appointment.appointment_date > today) |
                ((Appointment.appointment_date == today) & (Appointment.start_time >= now_time))
            )
            .order_by(Appointment.appointment_date, Appointment.start_time)
            .limit(limit)
        ).all()
    else:
        appts = session.exec(
            select(Appointment)
            .where(Appointment.patient_id == user.id)
            .where(Appointment.status.in_(["booked", "pending_approval"]))
            .where(
                (Appointment.appointment_date > today) |
                ((Appointment.appointment_date == today) & (Appointment.start_time >= now_time))
            )
            .order_by(Appointment.appointment_date, Appointment.start_time)
            .limit(limit)
        ).all()

    return [_appointment_out(a, session) for a in appts]

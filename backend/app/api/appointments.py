"""Appointments API – doctor availability & patient booking."""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.auth import AuthUser
from app.models.appointments import Appointment, DoctorAvailability, RegistrationRequest
from app.models.patient import Patient, Visit

router = APIRouter(prefix="/appointments", tags=["Appointments"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user_by_email(email: str, session: Session) -> AuthUser:
    user = session.exec(select(AuthUser).where(AuthUser.email == email.lower())).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def _require_doctor(user: AuthUser) -> None:
    if user.role != "doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can perform this action")


def _require_patient(user: AuthUser) -> None:
    if user.role != "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can perform this action")


def _parse_hhmm(t: str) -> tuple[int, int]:
    """Parse 'HH:MM' → (hour, minute). Raises ValueError on bad input."""
    parts = t.split(":")
    if len(parts) != 2:
        raise ValueError(f"Expected HH:MM, got '{t}'")
    return int(parts[0]), int(parts[1])


def _generate_slots(start_hhmm: str, end_hhmm: str, duration_minutes: int) -> List[tuple[str, str]]:
    """Return list of (start_time, end_time) HH:MM pairs for the given window."""
    sh, sm = _parse_hhmm(start_hhmm)
    eh, em = _parse_hhmm(end_hhmm)
    start = sh * 60 + sm
    end = eh * 60 + em
    slots = []
    cur = start
    while cur + duration_minutes <= end:
        nxt = cur + duration_minutes
        slots.append((f"{cur // 60:02d}:{cur % 60:02d}", f"{nxt // 60:02d}:{nxt % 60:02d}"))
        cur = nxt
    return slots


def _safe_tz(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, Exception):
        return ZoneInfo("UTC")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AvailabilitySlotIn(BaseModel):
    day_of_week: int          # 0=Monday … 6=Sunday
    start_time: str           # "HH:MM"
    end_time: str             # "HH:MM"
    timezone: str = "UTC"
    slot_duration_minutes: int = 30


class AvailabilitySlotOut(BaseModel):
    id: int
    day_of_week: int
    start_time: str
    end_time: str
    timezone: str
    slot_duration_minutes: int
    is_active: bool


class SetAvailabilityRequest(BaseModel):
    """Replace the doctor's entire availability schedule."""
    slots: List[AvailabilitySlotIn]


class DoctorOut(BaseModel):
    id: int
    full_name: str
    email: str


class TimeSlotOut(BaseModel):
    start_time: str
    end_time: str
    available: bool


class BookingRequest(BaseModel):
    doctor_id: int
    appointment_date: str   # "YYYY-MM-DD"
    start_time: str         # "HH:MM"
    end_time: str           # "HH:MM"
    timezone: str = "UTC"
    notes: Optional[str] = None
    request_registration: bool = False


class AppointmentOut(BaseModel):
    id: int
    doctor_id: int
    doctor_name: str
    patient_id: int
    patient_name: str
    appointment_date: str
    start_time: str
    end_time: str
    timezone: str
    status: str
    notes: Optional[str]
    created_at: datetime
    is_registered: bool = False
    rescheduled_by: Optional[str] = None
    cancelled_by: Optional[str] = None


class RescheduleRequest(BaseModel):
    appointment_date: str   # new date "YYYY-MM-DD"
    start_time: str         # new start "HH:MM"
    end_time: str           # new end "HH:MM"
    timezone: str = "UTC"


class RegistrationRequestOut(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    patient_email: str
    doctor_id: int
    appointment_id: Optional[int]
    appointment_date: Optional[str]
    appointment_start_time: Optional[str]
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Doctor: manage availability
# ---------------------------------------------------------------------------

@router.get("/availability/my", response_model=List[AvailabilitySlotOut])
def get_my_availability(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Return the authenticated doctor's availability slots."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_doctor(user)

    slots = session.exec(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == user.id)
        .where(DoctorAvailability.is_active == True)
        .order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time)
    ).all()

    return [
        AvailabilitySlotOut(
            id=s.id,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            timezone=s.timezone,
            slot_duration_minutes=s.slot_duration_minutes,
            is_active=s.is_active,
        )
        for s in slots
    ]


@router.post("/availability", response_model=List[AvailabilitySlotOut])
def set_availability(
    request: SetAvailabilityRequest,
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """
    Replace a doctor's full availability schedule.

    All existing active slots are soft-deleted and replaced with the new ones.
    """
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_doctor(user)

    # Validate input times
    for slot in request.slots:
        try:
            sh, sm = _parse_hhmm(slot.start_time)
            eh, em = _parse_hhmm(slot.end_time)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid time format in slot for day {slot.day_of_week}")
        if sh * 60 + sm >= eh * 60 + em:
            raise HTTPException(status_code=400, detail="start_time must be before end_time")
        if slot.day_of_week < 0 or slot.day_of_week > 6:
            raise HTTPException(status_code=400, detail="day_of_week must be 0–6")
        if slot.slot_duration_minutes < 10 or slot.slot_duration_minutes > 120:
            raise HTTPException(status_code=400, detail="slot_duration_minutes must be 10–120")

    # Soft-delete old slots
    old_slots = session.exec(
        select(DoctorAvailability).where(DoctorAvailability.doctor_id == user.id)
    ).all()
    for s in old_slots:
        s.is_active = False
        session.add(s)

    # Create new slots
    created = []
    for slot in request.slots:
        new_slot = DoctorAvailability(
            doctor_id=user.id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            timezone=slot.timezone,
            slot_duration_minutes=slot.slot_duration_minutes,
            is_active=True,
        )
        session.add(new_slot)
        created.append(new_slot)

    session.commit()
    for s in created:
        session.refresh(s)

    return [
        AvailabilitySlotOut(
            id=s.id,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            timezone=s.timezone,
            slot_duration_minutes=s.slot_duration_minutes,
            is_active=s.is_active,
        )
        for s in created
    ]


@router.delete("/availability/{slot_id}", status_code=204)
def delete_availability_slot(
    slot_id: int,
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Soft-delete a single availability slot."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_doctor(user)

    slot = session.get(DoctorAvailability, slot_id)
    if not slot or slot.doctor_id != user.id:
        raise HTTPException(status_code=404, detail="Slot not found")

    slot.is_active = False
    session.add(slot)
    session.commit()


# ---------------------------------------------------------------------------
# Patient: browse doctors & book slots
# ---------------------------------------------------------------------------

@router.get("/doctors", response_model=List[DoctorOut])
def list_doctors(session: Session = Depends(get_session)):
    """Return all registered doctors."""
    doctors = session.exec(
        select(AuthUser).where(AuthUser.role == "doctor").where(AuthUser.is_active == True)
    ).all()
    return [DoctorOut(id=d.id, full_name=d.full_name or d.email, email=d.email) for d in doctors]


@router.get("/doctors/{doctor_id}/availability", response_model=List[AvailabilitySlotOut])
def get_doctor_availability(doctor_id: int, session: Session = Depends(get_session)):
    """Return a specific doctor's active availability schedule."""
    doctor = session.get(AuthUser, doctor_id)
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")

    slots = session.exec(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == doctor_id)
        .where(DoctorAvailability.is_active == True)
        .order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time)
    ).all()

    return [
        AvailabilitySlotOut(
            id=s.id,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            timezone=s.timezone,
            slot_duration_minutes=s.slot_duration_minutes,
            is_active=s.is_active,
        )
        for s in slots
    ]


@router.get("/doctors/{doctor_id}/slots", response_model=List[TimeSlotOut])
def get_available_slots(
    doctor_id: int,
    date: Optional[str] = None,  # ?date=YYYY-MM-DD
    session: Session = Depends(get_session),
):
    """
    Return bookable time slots for a doctor on a specific date.

    Pass `?date=YYYY-MM-DD` as a query parameter.
    """
    target_date_str = date
    # validate date
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    doctor = session.get(AuthUser, doctor_id)
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")

    # day_of_week: Python weekday() → 0=Monday
    dow = target_date.weekday()

    availability = session.exec(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == doctor_id)
        .where(DoctorAvailability.day_of_week == dow)
        .where(DoctorAvailability.is_active == True)
    ).all()

    if not availability:
        return []

    # Generate all possible slots from availability windows
    all_slots: List[tuple[str, str]] = []
    for av in availability:
        all_slots.extend(_generate_slots(av.start_time, av.end_time, av.slot_duration_minutes))

    # Find already-booked slots for that date (including pending_approval)
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
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """
    Book an appointment for the authenticated patient.

    Returns 409 if the slot is already taken.
    """
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_patient(user)

    doctor = session.get(AuthUser, request.doctor_id)
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Validate date
    try:
        datetime.strptime(request.appointment_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Validate times
    try:
        sh, sm = _parse_hhmm(request.start_time)
        eh, em = _parse_hhmm(request.end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
    if sh * 60 + sm >= eh * 60 + em:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    # Atomic check-then-insert (within single transaction)
    existing = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == request.doctor_id)
        .where(Appointment.appointment_date == request.appointment_date)
        .where(Appointment.start_time == request.start_time)
        .where(Appointment.status.in_(["booked", "pending_approval"]))
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot not available. It has already been booked.",
        )

    # Verify the slot is within the doctor's declared availability
    dow = datetime.strptime(request.appointment_date, "%Y-%m-%d").weekday()
    slot_start_mins = sh * 60 + sm

    availability = session.exec(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == request.doctor_id)
        .where(DoctorAvailability.day_of_week == dow)
        .where(DoctorAvailability.is_active == True)
    ).all()

    if not availability:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No slots available. The doctor has not set working hours for this day.",
        )

    valid = False
    for av in availability:
        av_start = sum(int(x) * m for x, m in zip(av.start_time.split(":"), [60, 1]))
        av_end = sum(int(x) * m for x, m in zip(av.end_time.split(":"), [60, 1]))
        if av_start <= slot_start_mins and slot_start_mins < av_end:
            valid = True
            break

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected time is outside the doctor's availability.",
        )

    # Determine if this is a registration request (booking with a different doctor)
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
    session.flush()  # get appointment.id before commit

    if wants_registration:
        # Cancel any existing pending registration requests for this patient+doctor
        old_requests = session.exec(
            select(RegistrationRequest)
            .where(RegistrationRequest.patient_id == user.id)
            .where(RegistrationRequest.doctor_id == request.doctor_id)
            .where(RegistrationRequest.status == "pending")
        ).all()
        for old_req in old_requests:
            old_req.status = "superseded"
            session.add(old_req)

        reg_request = RegistrationRequest(
            patient_id=user.id,
            doctor_id=request.doctor_id,
            appointment_id=appointment.id,
            status="pending",
        )
        session.add(reg_request)

    session.commit()
    session.refresh(appointment)

    return _appointment_out(appointment, session)


# ---------------------------------------------------------------------------
# Shared: view, cancel, reschedule
# ---------------------------------------------------------------------------

def _appointment_out(appt: Appointment, session: Session) -> AppointmentOut:
    doctor = session.get(AuthUser, appt.doctor_id)
    patient = session.get(AuthUser, appt.patient_id)
    # Check if patient is registered with this doctor
    is_registered = False
    if patient and patient.patient_id:
        patient_record = session.get(Patient, patient.patient_id)
        if patient_record and patient_record.doctor_id == appt.doctor_id:
            is_registered = True
    return AppointmentOut(
        id=appt.id,
        doctor_id=appt.doctor_id,
        doctor_name=doctor.full_name if doctor else "Unknown",
        patient_id=appt.patient_id,
        patient_name=patient.full_name if patient else "Unknown",
        appointment_date=appt.appointment_date,
        start_time=appt.start_time,
        end_time=appt.end_time,
        timezone=appt.timezone,
        status=appt.status,
        notes=appt.notes,
        created_at=appt.created_at,
        is_registered=is_registered,
        rescheduled_by=appt.rescheduled_by,
        cancelled_by=appt.cancelled_by,
    )


@router.get("/my", response_model=List[AppointmentOut])
def get_my_appointments(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Return all appointments for the authenticated user (doctor or patient)."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)

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


@router.get("/upcoming", response_model=List[AppointmentOut])
def get_upcoming_appointments(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Return upcoming (future) appointments for the authenticated user."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)

    today = date.today().isoformat()

    if user.role == "doctor":
        appts = session.exec(
            select(Appointment)
            .where(Appointment.doctor_id == user.id)
            .where(Appointment.appointment_date >= today)
            .where(Appointment.status.in_(["booked", "pending_approval"]))
            .order_by(Appointment.appointment_date, Appointment.start_time)
        ).all()
    else:
        appts = session.exec(
            select(Appointment)
            .where(Appointment.patient_id == user.id)
            .where(Appointment.appointment_date >= today)
            .where(Appointment.status.in_(["booked", "pending_approval"]))
            .order_by(Appointment.appointment_date, Appointment.start_time)
        ).all()

    return [_appointment_out(a, session) for a in appts]


@router.get("/reschedule-notifications", response_model=List[AppointmentOut])
def get_reschedule_notifications(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Return appointments rescheduled by the OTHER party (unread reschedule notifications)."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    other_role = "patient" if user.role == "doctor" else "doctor"
    if user.role == "doctor":
        appts = session.exec(
            select(Appointment)
            .where(Appointment.doctor_id == user.id)
            .where(Appointment.rescheduled_by == other_role)
        ).all()
    else:
        appts = session.exec(
            select(Appointment)
            .where(Appointment.patient_id == user.id)
            .where(Appointment.rescheduled_by == other_role)
        ).all()
    return [_appointment_out(a, session) for a in appts]


@router.put("/dismiss-reschedule-notifications", status_code=204)
def dismiss_reschedule_notifications(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Clear all reschedule notifications for the current user."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    other_role = "patient" if user.role == "doctor" else "doctor"
    if user.role == "doctor":
        appts = session.exec(
            select(Appointment)
            .where(Appointment.doctor_id == user.id)
            .where(Appointment.rescheduled_by == other_role)
        ).all()
    else:
        appts = session.exec(
            select(Appointment)
            .where(Appointment.patient_id == user.id)
            .where(Appointment.rescheduled_by == other_role)
        ).all()
    for appt in appts:
        appt.rescheduled_by = None
        session.add(appt)
    session.commit()


@router.get("/cancel-notifications", response_model=List[AppointmentOut])
def get_cancel_notifications(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Return appointments cancelled by the OTHER party (unread cancel notifications)."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    other_role = "patient" if user.role == "doctor" else "doctor"
    if user.role == "doctor":
        appts = session.exec(
            select(Appointment)
            .where(Appointment.doctor_id == user.id)
            .where(Appointment.cancelled_by == other_role)
        ).all()
    else:
        appts = session.exec(
            select(Appointment)
            .where(Appointment.patient_id == user.id)
            .where(Appointment.cancelled_by == other_role)
        ).all()
    return [_appointment_out(a, session) for a in appts]


@router.put("/dismiss-cancel-notifications", status_code=204)
def dismiss_cancel_notifications(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Clear all cancel notifications for the current user."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    other_role = "patient" if user.role == "doctor" else "doctor"
    if user.role == "doctor":
        appts = session.exec(
            select(Appointment)
            .where(Appointment.doctor_id == user.id)
            .where(Appointment.cancelled_by == other_role)
        ).all()
    else:
        appts = session.exec(
            select(Appointment)
            .where(Appointment.patient_id == user.id)
            .where(Appointment.cancelled_by == other_role)
        ).all()
    for appt in appts:
        appt.cancelled_by = None
        session.add(appt)
    session.commit()


@router.put("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: int,
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Cancel an appointment. Both doctor and patient can cancel."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)

    appt = session.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appt.doctor_id != user.id and appt.patient_id != user.id:
        raise HTTPException(status_code=403, detail="Not your appointment")

    if appt.status not in ("booked", "pending_approval"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel an appointment with status '{appt.status}'")

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
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Reschedule an appointment to a new date/time."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)

    appt = session.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appt.doctor_id != user.id and appt.patient_id != user.id:
        raise HTTPException(status_code=403, detail="Not your appointment")

    if appt.status != "booked":
        raise HTTPException(status_code=400, detail=f"Cannot reschedule an appointment with status '{appt.status}'")

    # Validate new times
    try:
        datetime.strptime(request.appointment_date, "%Y-%m-%d")
        sh, sm = _parse_hhmm(request.start_time)
        eh, em = _parse_hhmm(request.end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format")

    if sh * 60 + sm >= eh * 60 + em:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    # Check no existing booking at the new slot
    conflict = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == appt.doctor_id)
        .where(Appointment.appointment_date == request.appointment_date)
        .where(Appointment.start_time == request.start_time)
        .where(Appointment.status == "booked")
        .where(Appointment.id != appointment_id)
    ).first()

    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot not available. It has already been booked.",
        )

    appt.appointment_date = request.appointment_date
    appt.start_time = request.start_time
    appt.end_time = request.end_time
    appt.timezone = request.timezone
    appt.status = "booked"
    appt.rescheduled_by = "doctor" if user.id == appt.doctor_id else "patient"
    appt.updated_at = datetime.utcnow()
    session.add(appt)
    session.commit()
    session.refresh(appt)
    return _appointment_out(appt, session)


# ---------------------------------------------------------------------------
# Patient: registered doctor
# ---------------------------------------------------------------------------

@router.get("/my-doctor", response_model=Optional[DoctorOut])
def get_my_doctor(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Return the patient's currently registered doctor, or null."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_patient(user)

    patient = session.get(Patient, user.patient_id) if user.patient_id else None

    if not patient or not patient.doctor_id:
        return None

    doctor = session.get(AuthUser, patient.doctor_id)
    if not doctor or doctor.role != "doctor":
        return None

    return DoctorOut(id=doctor.id, full_name=doctor.full_name or doctor.email, email=doctor.email)


@router.delete("/unregister", status_code=200)
def patient_unregister(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Patient unregisters themselves from their current doctor."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_patient(user)

    patient = session.get(Patient, user.patient_id) if user.patient_id else None
    if not patient or not patient.doctor_id:
        raise HTTPException(status_code=400, detail="You are not registered with any doctor")

    patient.doctor_id = None
    patient.clinical_notes = None
    session.add(patient)

    # Remove doctor-authored visit notes for unregistered patients.
    visits = session.exec(
        select(Visit).where(Visit.patient_id == patient.id)
    ).all()
    for v in visits:
        if v.visit_type != "clinical_notes":
            v.notes = None
            session.add(v)

    # Supersede any pending registration requests
    pending = session.exec(
        select(RegistrationRequest)
        .where(RegistrationRequest.patient_id == user.id)
        .where(RegistrationRequest.status == "pending")
    ).all()
    for req in pending:
        req.status = "superseded"
        session.add(req)

    session.commit()
    return {"detail": "Successfully unregistered"}


# ---------------------------------------------------------------------------
# Doctor: registration requests & registered patients
# ---------------------------------------------------------------------------

class RegisteredPatientOut(BaseModel):
    patient_auth_id: int
    patient_name: str
    patient_email: str
    patient_identifier: str


@router.get("/my-registered-patients", response_model=List[RegisteredPatientOut])
def get_my_registered_patients(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Return all patients currently registered under this doctor."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    doctor = _get_user_by_email(user_email, session)
    _require_doctor(doctor)

    patients = session.exec(
        select(Patient).where(Patient.doctor_id == doctor.id).order_by(Patient.name)
    ).all()

    result = []
    for p in patients:
        auth_user = session.exec(
            select(AuthUser).where(AuthUser.patient_id == p.id)
        ).first()
        result.append(RegisteredPatientOut(
            patient_auth_id=auth_user.id if auth_user else 0,
            patient_name=p.name,
            patient_email=auth_user.email if auth_user else "",
            patient_identifier=p.patient_identifier,
        ))
    return result


@router.delete("/unregister/{patient_auth_id}", status_code=200)
def doctor_unregister_patient(
    patient_auth_id: int,
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Doctor removes a patient from their registered list."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    doctor = _get_user_by_email(user_email, session)
    _require_doctor(doctor)

    patient_auth = session.get(AuthUser, patient_auth_id)
    if not patient_auth or patient_auth.role != "patient":
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = session.get(Patient, patient_auth.patient_id) if patient_auth.patient_id else None
    if not patient or patient.doctor_id != doctor.id:
        raise HTTPException(status_code=400, detail="This patient is not registered under you")

    patient.doctor_id = None
    patient.clinical_notes = None
    session.add(patient)

    visits = session.exec(
        select(Visit).where(Visit.patient_id == patient.id)
    ).all()
    for v in visits:
        if v.visit_type != "clinical_notes":
            v.notes = None
            session.add(v)

    # Supersede any pending registration requests for this doctor-patient pair
    pending = session.exec(
        select(RegistrationRequest)
        .where(RegistrationRequest.patient_id == patient_auth_id)
        .where(RegistrationRequest.doctor_id == doctor.id)
        .where(RegistrationRequest.status == "pending")
    ).all()
    for req in pending:
        req.status = "superseded"
        session.add(req)

    session.commit()
    return {"detail": "Patient successfully unregistered"}




@router.get("/registration-requests", response_model=List[RegistrationRequestOut])
def get_registration_requests(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Return all pending registration requests for the authenticated doctor."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_doctor(user)

    requests = session.exec(
        select(RegistrationRequest)
        .where(RegistrationRequest.doctor_id == user.id)
        .where(RegistrationRequest.status == "pending")
        .order_by(RegistrationRequest.created_at.desc())
    ).all()

    result = []
    for req in requests:
        patient_user = session.get(AuthUser, req.patient_id)
        appt = session.get(Appointment, req.appointment_id) if req.appointment_id else None
        result.append(RegistrationRequestOut(
            id=req.id,
            patient_id=req.patient_id,
            patient_name=patient_user.full_name if patient_user else "Unknown",
            patient_email=patient_user.email if patient_user else "",
            doctor_id=req.doctor_id,
            appointment_id=req.appointment_id,
            appointment_date=appt.appointment_date if appt else None,
            appointment_start_time=appt.start_time if appt else None,
            status=req.status,
            created_at=req.created_at,
        ))
    return result


@router.put("/registration-requests/{request_id}/approve", response_model=RegistrationRequestOut)
def approve_registration_request(
    request_id: int,
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """
    Approve a registration request.

    - Updates Patient.doctor_id to this doctor
    - Sets appointment status to 'booked'
    - Sets registration request status to 'approved'
    """
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    doctor = _get_user_by_email(user_email, session)
    _require_doctor(doctor)

    reg_req = session.get(RegistrationRequest, request_id)
    if not reg_req or reg_req.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Registration request not found")
    if reg_req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already '{reg_req.status}'")

    # Update patient's registered doctor
    patient_auth_user = session.get(AuthUser, reg_req.patient_id)
    if patient_auth_user and patient_auth_user.patient_id:
        patient_record = session.get(Patient, patient_auth_user.patient_id)
        if patient_record:
            patient_record.doctor_id = doctor.id
            session.add(patient_record)

    # Approve the linked appointment
    if reg_req.appointment_id:
        appt = session.get(Appointment, reg_req.appointment_id)
        if appt and appt.status == "pending_approval":
            appt.status = "booked"
            appt.updated_at = datetime.utcnow()
            session.add(appt)

    reg_req.status = "approved"
    reg_req.updated_at = datetime.utcnow()
    session.add(reg_req)
    session.commit()
    session.refresh(reg_req)

    patient_user = session.get(AuthUser, reg_req.patient_id)
    appt = session.get(Appointment, reg_req.appointment_id) if reg_req.appointment_id else None
    return RegistrationRequestOut(
        id=reg_req.id,
        patient_id=reg_req.patient_id,
        patient_name=patient_user.full_name if patient_user else "Unknown",
        patient_email=patient_user.email if patient_user else "",
        doctor_id=reg_req.doctor_id,
        appointment_id=reg_req.appointment_id,
        appointment_date=appt.appointment_date if appt else None,
        appointment_start_time=appt.start_time if appt else None,
        status=reg_req.status,
        created_at=reg_req.created_at,
    )


@router.put("/registration-requests/{request_id}/decline", response_model=RegistrationRequestOut)
def decline_registration_request(
    request_id: int,
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """
    Decline a registration request.

    - Sets appointment status to 'cancelled'
    - Sets registration request status to 'declined'
    """
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    doctor = _get_user_by_email(user_email, session)
    _require_doctor(doctor)

    reg_req = session.get(RegistrationRequest, request_id)
    if not reg_req or reg_req.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Registration request not found")
    if reg_req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already '{reg_req.status}'")

    # Cancel the linked appointment
    if reg_req.appointment_id:
        appt = session.get(Appointment, reg_req.appointment_id)
        if appt and appt.status == "pending_approval":
            appt.status = "cancelled"
            appt.updated_at = datetime.utcnow()
            session.add(appt)

    reg_req.status = "declined"
    reg_req.updated_at = datetime.utcnow()
    session.add(reg_req)
    session.commit()
    session.refresh(reg_req)

    patient_user = session.get(AuthUser, reg_req.patient_id)
    appt = session.get(Appointment, reg_req.appointment_id) if reg_req.appointment_id else None
    return RegistrationRequestOut(
        id=reg_req.id,
        patient_id=reg_req.patient_id,
        patient_name=patient_user.full_name if patient_user else "Unknown",
        patient_email=patient_user.email if patient_user else "",
        doctor_id=reg_req.doctor_id,
        appointment_id=reg_req.appointment_id,
        appointment_date=appt.appointment_date if appt else None,
        appointment_start_time=appt.start_time if appt else None,
        status=reg_req.status,
        created_at=reg_req.created_at,
    )


# ---------------------------------------------------------------------------
# Patient: view own registration request outcomes
# ---------------------------------------------------------------------------

@router.get("/my-registration-requests", response_model=List[RegistrationRequestOut])
def get_my_registration_requests(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Return the patient's own registration requests so they can see outcomes."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_patient(user)

    reqs = session.exec(
        select(RegistrationRequest)
        .where(RegistrationRequest.patient_id == user.id)
        .where(RegistrationRequest.status.in_(["pending", "approved", "declined"]))
        .order_by(RegistrationRequest.updated_at.desc())
    ).all()

    result = []
    for req in reqs:
        doctor_user = session.get(AuthUser, req.doctor_id)
        appt = session.get(Appointment, req.appointment_id) if req.appointment_id else None
        result.append(RegistrationRequestOut(
            id=req.id,
            patient_id=req.patient_id,
            patient_name=doctor_user.full_name or doctor_user.email if doctor_user else "Unknown Doctor",
            patient_email=doctor_user.email if doctor_user else "",
            doctor_id=req.doctor_id,
            appointment_id=req.appointment_id,
            appointment_date=appt.appointment_date if appt else None,
            appointment_start_time=appt.start_time if appt else None,
            status=req.status,
            created_at=req.created_at,
        ))
    return result

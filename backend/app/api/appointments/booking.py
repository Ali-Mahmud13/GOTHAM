from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.security import get_current_user_compat
from app.db.session import get_session
from app.models.appointments import Appointment
from app.models.auth import AuthUser
from app.models.patient import Patient

from .schemas import (
    AppointmentOut,
    AppointmentOutcomeRequest,
    BookingRequest,
    RescheduleRequest,
    TimeSlotOut,
)
from .utils import (
    ACTIVE_APPOINTMENT_STATUSES,
    BOOKING_HORIZON_DAYS,
    _appointment_is_elapsed,
    _appointment_is_future,
    _appointment_out,
    _effective_windows_for_date,
    _generate_slots,
    _local_slot_to_utc,
    _reconcile_elapsed_appointments,
    _require_doctor,
    _require_patient,
    _schedule_timezone_for_date,
    _validate_booking_window,
    _validate_slot_against_availability,
)

router = APIRouter()


def _naive_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _user_appointments(session: Session, user: AuthUser) -> list[Appointment]:
    statement = select(Appointment)
    if user.role == "doctor":
        statement = statement.where(Appointment.doctor_id == user.id)
    else:
        statement = statement.where(Appointment.patient_id == user.id)
    return list(
        session.exec(
            statement.order_by(Appointment.appointment_date, Appointment.start_time)
        ).all()
    )


@router.get("/doctors/{doctor_id}/slots", response_model=List[TimeSlotOut])
def get_available_slots(
    doctor_id: int,
    date: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Return slots in the doctor's schedule timezone plus UTC instants."""
    try:
        target_date = datetime.strptime(date or "", "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD") from exc

    doctor = session.get(AuthUser, doctor_id)
    if (
        not doctor
        or doctor.role != "doctor"
        or not doctor.is_active
        or doctor.verification_status != "verified"
    ):
        raise HTTPException(status_code=404, detail="Doctor not found or unavailable.")

    schedule_timezone = _schedule_timezone_for_date(session, doctor_id, date)
    windows = _effective_windows_for_date(session, doctor_id, date)
    if not windows:
        return []

    booked = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == doctor_id)
        .where(Appointment.appointment_date == date)
        .where(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
    ).all()
    booked_starts = {appointment.start_time for appointment in booked}

    result: list[TimeSlotOut] = []
    for window_start, window_end, duration in windows:
        for start_time, end_time in _generate_slots(window_start, window_end, duration):
            start_at, end_at = _local_slot_to_utc(
                date, start_time, end_time, schedule_timezone
            )
            within_horizon = (
                datetime.now(timezone.utc)
                <= start_at
                <= datetime.now(timezone.utc)
                + timedelta(days=BOOKING_HORIZON_DAYS)
            )
            result.append(
                TimeSlotOut(
                    start_time=start_time,
                    end_time=end_time,
                    available=start_time not in booked_starts and within_horizon,
                    schedule_timezone=schedule_timezone,
                    start_at_utc=start_at,
                    end_at_utc=end_at,
                )
            )
    return result


@router.post("/book", response_model=AppointmentOut, status_code=201)
def book_appointment(
    request: BookingRequest,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Book with the authenticated patient's assigned doctor."""
    _require_patient(user)
    doctor = session.get(AuthUser, request.doctor_id)
    if (
        not doctor
        or doctor.role != "doctor"
        or not doctor.is_active
        or doctor.verification_status != "verified"
    ):
        raise HTTPException(status_code=404, detail="Doctor not found or not accepting appointments.")

    patient = session.get(Patient, user.patient_id) if user.patient_id else None
    if not patient or patient.doctor_id != request.doctor_id:
        raise HTTPException(
            status_code=403,
            detail="You may only book appointments with your registered doctor.",
        )

    _validate_slot_against_availability(
        session,
        request.doctor_id,
        request.appointment_date,
        request.start_time,
        request.end_time,
    )
    schedule_timezone = _schedule_timezone_for_date(
        session, request.doctor_id, request.appointment_date
    )
    start_at, end_at = _local_slot_to_utc(
        request.appointment_date,
        request.start_time,
        request.end_time,
        schedule_timezone,
    )
    _validate_booking_window(start_at)

    existing = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == request.doctor_id)
        .where(Appointment.appointment_date == request.appointment_date)
        .where(Appointment.start_time == request.start_time)
        .where(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Time slot not available.")

    appointment = Appointment(
        doctor_id=request.doctor_id,
        patient_id=user.id,
        appointment_date=request.appointment_date,
        start_time=request.start_time,
        end_time=request.end_time,
        timezone=schedule_timezone,
        schedule_timezone=schedule_timezone,
        start_at_utc=_naive_utc(start_at),
        end_at_utc=_naive_utc(end_at),
        status="booked",
        notes=request.notes,
    )
    session.add(appointment)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="Slot just got booked.") from exc
    session.refresh(appointment)
    return _appointment_out(appointment, session)


@router.get("/my", response_model=List[AppointmentOut])
def get_my_appointments(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    appointments = _user_appointments(session, user)
    _reconcile_elapsed_appointments(session, appointments)
    return [_appointment_out(appointment, session) for appointment in appointments]


@router.put("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: int,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    appointment = session.get(Appointment, appointment_id)
    if not appointment or (
        appointment.doctor_id != user.id and appointment.patient_id != user.id
    ):
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status not in ACTIVE_APPOINTMENT_STATUSES:
        raise HTTPException(status_code=400, detail="This appointment cannot be cancelled.")
    if _appointment_is_elapsed(appointment):
        raise HTTPException(status_code=409, detail="Elapsed appointments cannot be cancelled.")

    appointment.status = "cancelled"
    appointment.cancelled_by = "doctor" if user.id == appointment.doctor_id else "patient"
    appointment.cancellation_reason = "cancelled_by_user"
    appointment.updated_at = datetime.utcnow()
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return _appointment_out(appointment, session)


@router.put("/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule_appointment(
    appointment_id: int,
    request: RescheduleRequest,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    appointment = session.get(Appointment, appointment_id)
    if not appointment or (
        appointment.doctor_id != user.id and appointment.patient_id != user.id
    ):
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status not in ACTIVE_APPOINTMENT_STATUSES:
        raise HTTPException(status_code=400, detail="This appointment cannot be rescheduled.")
    if _appointment_is_elapsed(appointment):
        raise HTTPException(status_code=409, detail="Elapsed appointments cannot be rescheduled.")

    _validate_slot_against_availability(
        session,
        appointment.doctor_id,
        request.appointment_date,
        request.start_time,
        request.end_time,
    )
    schedule_timezone = _schedule_timezone_for_date(
        session, appointment.doctor_id, request.appointment_date
    )
    start_at, end_at = _local_slot_to_utc(
        request.appointment_date,
        request.start_time,
        request.end_time,
        schedule_timezone,
    )
    _validate_booking_window(start_at)

    conflict = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == appointment.doctor_id)
        .where(Appointment.appointment_date == request.appointment_date)
        .where(Appointment.start_time == request.start_time)
        .where(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
        .where(Appointment.id != appointment.id)
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail="That slot is already booked.")

    appointment.appointment_date = request.appointment_date
    appointment.start_time = request.start_time
    appointment.end_time = request.end_time
    appointment.timezone = schedule_timezone
    appointment.schedule_timezone = schedule_timezone
    appointment.start_at_utc = _naive_utc(start_at)
    appointment.end_at_utc = _naive_utc(end_at)
    appointment.rescheduled_by = "doctor" if user.id == appointment.doctor_id else "patient"
    appointment.updated_at = datetime.utcnow()
    session.add(appointment)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="That slot was just booked.") from exc
    session.refresh(appointment)
    return _appointment_out(appointment, session)


@router.put("/{appointment_id}/outcome", response_model=AppointmentOut)
def record_appointment_outcome(
    appointment_id: int,
    request: AppointmentOutcomeRequest,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    _require_doctor(user)
    appointment = session.get(Appointment, appointment_id)
    if not appointment or appointment.doctor_id != user.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status == "booked" and _appointment_is_elapsed(appointment):
        appointment.status = "awaiting_outcome"
    if appointment.status != "awaiting_outcome":
        raise HTTPException(
            status_code=409,
            detail="Only elapsed appointments awaiting an outcome can be completed.",
        )
    appointment.status = request.outcome
    appointment.outcome_recorded_at = datetime.utcnow()
    appointment.outcome_recorded_by = user.id
    appointment.updated_at = datetime.utcnow()
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return _appointment_out(appointment, session)


@router.get("/upcoming", response_model=List[AppointmentOut])
def get_upcoming_appointments(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
    limit: int = 5,
):
    appointments = _user_appointments(session, user)
    _reconcile_elapsed_appointments(session, appointments)
    upcoming = [
        appointment
        for appointment in appointments
        if appointment.status in ACTIVE_APPOINTMENT_STATUSES
        and _appointment_is_future(appointment)
    ][: max(1, min(limit, 50))]
    return [_appointment_out(appointment, session) for appointment in upcoming]

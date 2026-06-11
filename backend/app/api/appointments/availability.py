from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_session
from app.core.security import get_current_user_compat
from app.models.auth import AuthUser
from app.models.appointments import DoctorAvailability, DoctorScheduleException, Appointment

from .schemas import (
    AvailabilitySlotOut, SetAvailabilityRequest, ScheduleExceptionIn,
    ScheduleExceptionOut, ScheduleExceptionCreatedOut, BookingConfigOut
)
from .utils import (
    _require_doctor, _parse_hhmm, _hhmm_to_mins, _collect_future_appointment_conflicts_for_recurring_change,
    _validate_custom_windows_no_overlap, BOOKING_HORIZON_DAYS, MIN_BOOKING_LEAD_HOURS
)

router = APIRouter()

def _schedule_exception_to_out(row: DoctorScheduleException) -> ScheduleExceptionOut:
    return ScheduleExceptionOut(
        id=row.id,
        doctor_id=row.doctor_id,
        exception_date=row.exception_date,
        kind=row.kind,
        start_time=row.start_time,
        end_time=row.end_time,
        slot_duration_minutes=row.slot_duration_minutes,
        timezone=row.timezone,
        notes=row.notes,
        created_at=row.created_at,
    )


@router.get("/booking-config", response_model=BookingConfigOut)
def get_booking_config():
    """Public: patient booking horizon and minimum lead time."""
    return BookingConfigOut(
        booking_horizon_days=BOOKING_HORIZON_DAYS,
        min_booking_lead_hours=MIN_BOOKING_LEAD_HOURS,
    )


@router.get("/availability/my", response_model=List[AvailabilitySlotOut])
def get_my_availability(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return the authenticated doctor's availability slots."""
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
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Replace a doctor's full availability schedule."""
    _require_doctor(user)

    normalized_by_day = {d: [] for d in range(7)}
    for slot in request.slots:
        try:
            sh, sm = _parse_hhmm(slot.start_time)
            eh, em = _parse_hhmm(slot.end_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format.")
        if sh * 60 + sm >= eh * 60 + em:
            raise HTTPException(status_code=400, detail="start_time must be before end_time")
        normalized_by_day[slot.day_of_week].append((_hhmm_to_mins(slot.start_time), _hhmm_to_mins(slot.end_time)))

    for dow, windows in normalized_by_day.items():
        _validate_custom_windows_no_overlap(windows)

    conflicts = _collect_future_appointment_conflicts_for_recurring_change(session, user.id, request.slots)
    if conflicts:
        raise HTTPException(status_code=409, detail="Conflicts detected.")

    old_slots = session.exec(
        select(DoctorAvailability).where(DoctorAvailability.doctor_id == user.id)
    ).all()
    for s in old_slots:
        s.is_active = False
        session.add(s)

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
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Soft-delete a single availability slot."""
    _require_doctor(user)
    slot = session.get(DoctorAvailability, slot_id)
    if not slot or slot.doctor_id != user.id:
        raise HTTPException(status_code=404, detail="Slot not found")
    slot.is_active = False
    session.add(slot)
    session.commit()


@router.post("/exceptions", response_model=ScheduleExceptionCreatedOut, status_code=201)
def create_schedule_exception(
    body: ScheduleExceptionIn,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Create a per-date schedule exception. Returns any impacted appointments on blocked dates."""
    _require_doctor(user)
    kind = body.kind.strip().lower()
    if kind not in ("blocked", "custom"):
        raise HTTPException(status_code=400, detail="kind must be 'blocked' or 'custom'")

    if kind == "blocked":
        row = DoctorScheduleException(
            doctor_id=user.id,
            exception_date=body.exception_date,
            kind="blocked",
            timezone=body.timezone,
            notes=body.notes,
        )
        session.add(row)
        session.commit()
        session.refresh(row)

        # Find existing booked/pending appointments on this date so the doctor is warned.
        from app.models.appointments import Appointment
        from sqlmodel import select as sq_select
        from app.models.auth import AuthUser as _AuthUser
        impacted = session.exec(
            sq_select(Appointment)
            .where(Appointment.doctor_id == user.id)
            .where(Appointment.appointment_date == body.exception_date)
            .where(Appointment.status.in_(["booked", "pending_approval"]))
        ).all()
        from .schemas import AvailabilityConflictOut
        impacted_out = [
            AvailabilityConflictOut(
                appointment_id=a.id,
                appointment_date=a.appointment_date,
                start_time=a.start_time,
                end_time=a.end_time,
                patient_id=a.patient_id,
                patient_name=(
                    (session.get(_AuthUser, a.patient_id) or _AuthUser()).full_name or "Unknown"
                ),
            )
            for a in impacted
        ]
        return ScheduleExceptionCreatedOut(
            exception=_schedule_exception_to_out(row),
            impacted_appointments=impacted_out,
        )

    # custom logic
    if not body.start_time or not body.end_time:
        raise HTTPException(status_code=400, detail="start/end required for custom")

    row = DoctorScheduleException(
        doctor_id=user.id,
        exception_date=body.exception_date,
        kind="custom",
        start_time=body.start_time,
        end_time=body.end_time,
        slot_duration_minutes=body.slot_duration_minutes,
        timezone=body.timezone,
        notes=body.notes,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return ScheduleExceptionCreatedOut(
        exception=_schedule_exception_to_out(row),
        impacted_appointments=[],
    )


@router.get("/exceptions/my", response_model=List[ScheduleExceptionOut])
def list_my_schedule_exceptions(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """List my exceptions."""
    _require_doctor(user)
    q = select(DoctorScheduleException).where(DoctorScheduleException.doctor_id == user.id)
    rows = session.exec(q).all()
    return [_schedule_exception_to_out(r) for r in rows]


@router.delete("/exceptions/{exception_id}", status_code=204)
def delete_schedule_exception(
    exception_id: int,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Delete an exception."""
    _require_doctor(user)
    row = session.get(DoctorScheduleException, exception_id)
    if not row or row.doctor_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(row)
    session.commit()


@router.get("/doctors/{doctor_id}/availability", response_model=List[AvailabilitySlotOut])
def get_doctor_availability(
    doctor_id: int,
    session: Session = Depends(get_session),
):
    """Public: Return a doctor's regular availability slots."""
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


@router.get("/doctors/{doctor_id}/exceptions", response_model=List[ScheduleExceptionOut])
def get_doctor_exceptions(
    doctor_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Public: Return a doctor's schedule exceptions within a date range."""
    q = select(DoctorScheduleException).where(DoctorScheduleException.doctor_id == doctor_id)
    if date_from:
        q = q.where(DoctorScheduleException.exception_date >= date_from)
    if date_to:
        q = q.where(DoctorScheduleException.exception_date <= date_to)
    
    rows = session.exec(q.order_by(DoctorScheduleException.exception_date)).all()
    return [_schedule_exception_to_out(r) for r in rows]

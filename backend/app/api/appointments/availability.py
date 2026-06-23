from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import get_current_user_compat
from app.db.session import get_session
from app.models.appointments import (
    Appointment,
    DoctorAvailability,
    DoctorScheduleException,
)
from app.models.auth import AuthUser

from .schemas import (
    AvailabilityConflictOut,
    AvailabilitySlotIn,
    AvailabilitySlotOut,
    BookingConfigOut,
    ScheduleExceptionCreatedOut,
    ScheduleExceptionIn,
    ScheduleExceptionOut,
    SetAvailabilityRequest,
)
from .utils import (
    ACTIVE_APPOINTMENT_STATUSES,
    BOOKING_HORIZON_DAYS,
    MIN_BOOKING_LEAD_HOURS,
    _appointment_is_future,
    _appointment_matches_effective_schedule,
    _collect_future_appointment_conflicts_for_recurring_change,
    _conflict_out,
    _hhmm_to_mins,
    _require_doctor,
    _validate_custom_windows_no_overlap,
)

router = APIRouter()


def _availability_out(row: DoctorAvailability) -> AvailabilitySlotOut:
    return AvailabilitySlotOut(
        id=row.id,
        day_of_week=row.day_of_week,
        start_time=row.start_time,
        end_time=row.end_time,
        timezone=row.timezone,
        slot_duration_minutes=row.slot_duration_minutes,
        is_active=row.is_active,
    )


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


def _conflict_detail(conflicts: list[AvailabilityConflictOut]) -> dict:
    return {
        "message": "Schedule change conflicts with future appointments.",
        "conflicts": [conflict.model_dump() for conflict in conflicts],
    }


def _doctor_schedule_timezone(session: Session, doctor_id: int) -> Optional[str]:
    slot = session.exec(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == doctor_id)
        .where(DoctorAvailability.is_active == True)
    ).first()
    return slot.timezone if slot else None


@router.get("/booking-config", response_model=BookingConfigOut)
def get_booking_config():
    return BookingConfigOut(
        booking_horizon_days=BOOKING_HORIZON_DAYS,
        min_booking_lead_hours=MIN_BOOKING_LEAD_HOURS,
    )


@router.get("/availability/my", response_model=List[AvailabilitySlotOut])
def get_my_availability(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    _require_doctor(user)
    rows = session.exec(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == user.id)
        .where(DoctorAvailability.is_active == True)
        .order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time)
    ).all()
    return [_availability_out(row) for row in rows]


@router.post("/availability", response_model=List[AvailabilitySlotOut])
def set_availability(
    request: SetAvailabilityRequest,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    _require_doctor(user)
    by_day = {day: [] for day in range(7)}
    for slot in request.slots:
        by_day[slot.day_of_week].append(
            (_hhmm_to_mins(slot.start_time), _hhmm_to_mins(slot.end_time))
        )
    for windows in by_day.values():
        _validate_custom_windows_no_overlap(windows)

    conflicts = _collect_future_appointment_conflicts_for_recurring_change(
        session, user.id, request.slots
    )
    if conflicts:
        raise HTTPException(status_code=409, detail=_conflict_detail(conflicts))

    old_slots = session.exec(
        select(DoctorAvailability).where(DoctorAvailability.doctor_id == user.id)
    ).all()
    for row in old_slots:
        row.is_active = False
        session.add(row)

    created: list[DoctorAvailability] = []
    for slot in request.slots:
        row = DoctorAvailability(
            doctor_id=user.id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            timezone=slot.timezone,
            slot_duration_minutes=slot.slot_duration_minutes,
            is_active=True,
        )
        session.add(row)
        created.append(row)
    session.commit()
    for row in created:
        session.refresh(row)
    return [_availability_out(row) for row in created]


@router.delete("/availability/{slot_id}", status_code=204)
def delete_availability_slot(
    slot_id: int,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    _require_doctor(user)
    slot = session.get(DoctorAvailability, slot_id)
    if not slot or slot.doctor_id != user.id or not slot.is_active:
        raise HTTPException(status_code=404, detail="Slot not found")

    remaining_rows = session.exec(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == user.id)
        .where(DoctorAvailability.is_active == True)
        .where(DoctorAvailability.id != slot.id)
    ).all()
    remaining = [
        AvailabilitySlotIn(
            day_of_week=row.day_of_week,
            start_time=row.start_time,
            end_time=row.end_time,
            timezone=row.timezone,
            slot_duration_minutes=row.slot_duration_minutes,
        )
        for row in remaining_rows
    ]
    conflicts = _collect_future_appointment_conflicts_for_recurring_change(
        session, user.id, remaining
    )
    if conflicts:
        raise HTTPException(status_code=409, detail=_conflict_detail(conflicts))
    slot.is_active = False
    session.add(slot)
    session.commit()


@router.post("/exceptions", response_model=ScheduleExceptionCreatedOut, status_code=201)
def create_schedule_exception(
    body: ScheduleExceptionIn,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    _require_doctor(user)
    schedule_timezone = _doctor_schedule_timezone(session, user.id)
    if schedule_timezone and body.timezone != schedule_timezone:
        raise HTTPException(
            status_code=400,
            detail=f"Schedule exceptions must use the schedule timezone ({schedule_timezone}).",
        )

    duplicate = session.exec(
        select(DoctorScheduleException)
        .where(DoctorScheduleException.doctor_id == user.id)
        .where(DoctorScheduleException.exception_date == body.exception_date)
        .where(DoctorScheduleException.kind == body.kind)
        .where(DoctorScheduleException.start_time == body.start_time)
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="This schedule exception already exists.")

    row = DoctorScheduleException(
        doctor_id=user.id,
        exception_date=body.exception_date,
        kind=body.kind,
        start_time=body.start_time,
        end_time=body.end_time,
        slot_duration_minutes=body.slot_duration_minutes if body.kind == "custom" else None,
        timezone=body.timezone,
        notes=body.notes,
    )
    session.add(row)
    session.flush()

    if body.kind == "custom":
        custom_rows = session.exec(
            select(DoctorScheduleException)
            .where(DoctorScheduleException.doctor_id == user.id)
            .where(DoctorScheduleException.exception_date == body.exception_date)
            .where(DoctorScheduleException.kind == "custom")
        ).all()
        _validate_custom_windows_no_overlap(
            [
                (_hhmm_to_mins(item.start_time), _hhmm_to_mins(item.end_time))
                for item in custom_rows
                if item.start_time and item.end_time
            ]
        )

    appointments = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == user.id)
        .where(Appointment.appointment_date == body.exception_date)
        .where(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
    ).all()
    conflicts = [
        _conflict_out(session, appointment)
        for appointment in appointments
        if _appointment_is_future(appointment)
        and not _appointment_matches_effective_schedule(session, user.id, appointment)
    ]
    if conflicts:
        session.rollback()
        raise HTTPException(status_code=409, detail=_conflict_detail(conflicts))

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
    _require_doctor(user)
    rows = session.exec(
        select(DoctorScheduleException)
        .where(DoctorScheduleException.doctor_id == user.id)
        .order_by(DoctorScheduleException.exception_date, DoctorScheduleException.start_time)
    ).all()
    return [_schedule_exception_to_out(row) for row in rows]


@router.delete("/exceptions/{exception_id}", status_code=204)
def delete_schedule_exception(
    exception_id: int,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    _require_doctor(user)
    row = session.get(DoctorScheduleException, exception_id)
    if not row or row.doctor_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    exception_date = row.exception_date
    session.delete(row)
    session.flush()
    appointments = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == user.id)
        .where(Appointment.appointment_date == exception_date)
        .where(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
    ).all()
    conflicts = [
        _conflict_out(session, appointment)
        for appointment in appointments
        if _appointment_is_future(appointment)
        and not _appointment_matches_effective_schedule(session, user.id, appointment)
    ]
    if conflicts:
        session.rollback()
        raise HTTPException(status_code=409, detail=_conflict_detail(conflicts))
    session.commit()


@router.get("/doctors/{doctor_id}/availability", response_model=List[AvailabilitySlotOut])
def get_doctor_availability(
    doctor_id: int,
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == doctor_id)
        .where(DoctorAvailability.is_active == True)
        .order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time)
    ).all()
    return [_availability_out(row) for row in rows]


@router.get("/doctors/{doctor_id}/exceptions", response_model=List[ScheduleExceptionOut])
def get_doctor_exceptions(
    doctor_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session),
):
    statement = select(DoctorScheduleException).where(
        DoctorScheduleException.doctor_id == doctor_id
    )
    if date_from:
        try:
            datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="date_from must use YYYY-MM-DD") from exc
        statement = statement.where(DoctorScheduleException.exception_date >= date_from)
    if date_to:
        try:
            datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="date_to must use YYYY-MM-DD") from exc
        statement = statement.where(DoctorScheduleException.exception_date <= date_to)
    rows = session.exec(
        statement.order_by(
            DoctorScheduleException.exception_date,
            DoctorScheduleException.start_time,
        )
    ).all()
    return [_schedule_exception_to_out(row) for row in rows]

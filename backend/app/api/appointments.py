"""Appointments API – doctor availability & patient booking."""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.auth import AuthUser
from app.models.appointments import (
    Appointment,
    DoctorAvailability,
    DoctorNotificationState,
    DoctorScheduleException,
    RegistrationRequest,
)
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


def _is_past(appointment_date: str, start_time: str, tz_name: str) -> bool:
    """True if appointment start (in given IANA tz) is strictly before now in that zone."""
    zone = _safe_tz(tz_name)
    try:
        dt = datetime.strptime(f"{appointment_date} {start_time}", "%Y-%m-%d %H:%M").replace(tzinfo=zone)
    except ValueError:
        return True
    return dt < datetime.now(tz=zone)


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


class AvailabilityConflictOut(BaseModel):
    appointment_id: int
    appointment_date: str
    start_time: str
    end_time: str
    patient_id: int
    patient_name: str


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


BOOKING_HORIZON_DAYS = 14


class ScheduleExceptionIn(BaseModel):
    exception_date: str  # YYYY-MM-DD
    kind: str  # blocked | custom
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    slot_duration_minutes: Optional[int] = 30
    timezone: str = "UTC"
    notes: Optional[str] = None


class ScheduleExceptionOut(BaseModel):
    id: int
    doctor_id: int
    exception_date: str
    kind: str
    start_time: Optional[str]
    end_time: Optional[str]
    slot_duration_minutes: Optional[int]
    timezone: str
    notes: Optional[str]
    created_at: datetime


class BookingConfigOut(BaseModel):
    booking_horizon_days: int


class NewBookingNotificationsOut(BaseModel):
    count: int


def _hhmm_to_mins(hhmm: str) -> int:
    h, m = _parse_hhmm(hhmm)
    return h * 60 + m


def _effective_windows_for_date(
    session: Session,
    doctor_id: int,
    target_date_str: str,
    recurring_slots_override: Optional[List[AvailabilitySlotIn]] = None,
) -> Optional[List[tuple[str, str, int]]]:
    """
    None = date fully blocked.
    [] = no applicable windows.
    Otherwise list of (start_hhmm, end_hhmm, slot_duration_minutes).
    """
    blocked = session.exec(
        select(DoctorScheduleException)
        .where(DoctorScheduleException.doctor_id == doctor_id)
        .where(DoctorScheduleException.exception_date == target_date_str)
        .where(DoctorScheduleException.kind == "blocked")
    ).first()
    if blocked:
        return None

    customs = session.exec(
        select(DoctorScheduleException)
        .where(DoctorScheduleException.doctor_id == doctor_id)
        .where(DoctorScheduleException.exception_date == target_date_str)
        .where(DoctorScheduleException.kind == "custom")
        .order_by(DoctorScheduleException.id)
    ).all()
    if customs:
        out: List[tuple[str, str, int]] = []
        for c in customs:
            if not c.start_time or not c.end_time:
                continue
            dur = c.slot_duration_minutes or 30
            out.append((c.start_time, c.end_time, dur))
        return out

    try:
        d = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        return []
    dow = d.weekday()

    if recurring_slots_override is not None:
        rows = [s for s in recurring_slots_override if s.day_of_week == dow]
        if not rows:
            return []
        return [(s.start_time, s.end_time, s.slot_duration_minutes) for s in rows]

    availability = session.exec(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == doctor_id)
        .where(DoctorAvailability.day_of_week == dow)
        .where(DoctorAvailability.is_active == True)
    ).all()
    if not availability:
        return []
    return [(av.start_time, av.end_time, av.slot_duration_minutes) for av in availability]


def _slot_times_fit_windows(start_mins: int, end_mins: int, windows: List[tuple[str, str, int]]) -> bool:
    for st_s, en_s, dur in windows:
        try:
            av_start = _hhmm_to_mins(st_s)
            av_end = _hhmm_to_mins(en_s)
        except ValueError:
            continue
        if dur <= 0:
            continue
        if av_start <= start_mins and end_mins <= av_end:
            if (start_mins - av_start) % dur == 0 and (end_mins - start_mins) == dur:
                return True
    return False


def _validate_slot_against_availability(
    session: Session,
    doctor_id: int,
    appointment_date: str,
    start_time: str,
    end_time: str,
) -> None:
    try:
        datetime.strptime(appointment_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    try:
        sh, sm = _parse_hhmm(start_time)
        eh, em = _parse_hhmm(end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    start_mins = sh * 60 + sm
    end_mins = eh * 60 + em
    if start_mins >= end_mins:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    wins = _effective_windows_for_date(session, doctor_id, appointment_date, recurring_slots_override=None)
    if wins is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The doctor is not available on this date.",
        )
    if not wins:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No slots available. The doctor has not set working hours for this day.",
        )
    if not _slot_times_fit_windows(start_mins, end_mins, wins):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected time is outside the doctor's availability or not aligned to the slot grid.",
        )


def _appointment_matches_effective_schedule(
    session: Session,
    doctor_id: int,
    appt: Appointment,
    *,
    recurring_slots_override: Optional[List[AvailabilitySlotIn]] = None,
) -> bool:
    if _is_past(appt.appointment_date, appt.start_time, appt.timezone):
        return True
    try:
        sh, sm = _parse_hhmm(appt.start_time)
        eh, em = _parse_hhmm(appt.end_time)
    except ValueError:
        return False
    start_mins = sh * 60 + sm
    end_mins = eh * 60 + em
    if start_mins >= end_mins:
        return False
    wins = _effective_windows_for_date(
        session, doctor_id, appt.appointment_date, recurring_slots_override=recurring_slots_override
    )
    if wins is None:
        return False
    if not wins:
        return False
    return _slot_times_fit_windows(start_mins, end_mins, wins)


def _collect_future_appointment_conflicts_for_recurring_change(
    session: Session, doctor_id: int, recurring_slots: List[AvailabilitySlotIn]
) -> list[AvailabilityConflictOut]:
    today = date.today().isoformat()
    future_appts = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == doctor_id)
        .where(Appointment.appointment_date >= today)
        .where(Appointment.status.in_(["booked", "pending_approval"]))
        .order_by(Appointment.appointment_date, Appointment.start_time)
    ).all()
    conflicts: list[AvailabilityConflictOut] = []
    for appt in future_appts:
        if not _appointment_matches_effective_schedule(
            session, doctor_id, appt, recurring_slots_override=recurring_slots
        ):
            patient_user = session.get(AuthUser, appt.patient_id)
            conflicts.append(
                AvailabilityConflictOut(
                    appointment_id=appt.id,
                    appointment_date=appt.appointment_date,
                    start_time=appt.start_time,
                    end_time=appt.end_time,
                    patient_id=appt.patient_id,
                    patient_name=(patient_user.full_name if patient_user else "Unknown"),
                )
            )
    return conflicts


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


# ---------------------------------------------------------------------------
# Doctor: manage availability
# ---------------------------------------------------------------------------

@router.get("/booking-config", response_model=BookingConfigOut)
def get_booking_config():
    """Public: patient booking horizon (days from today)."""
    return BookingConfigOut(booking_horizon_days=BOOKING_HORIZON_DAYS)


@router.get("/new-booking-notifications", response_model=NewBookingNotificationsOut)
def get_new_booking_notifications(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Doctor-only: count of newly created appointments since last dismissal."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_doctor(user)

    state = session.get(DoctorNotificationState, user.id)
    if not state:
        state = DoctorNotificationState(doctor_id=user.id)
        session.add(state)
        session.commit()
        session.refresh(state)

    count = session.exec(
        select(Appointment.id)
        .where(Appointment.doctor_id == user.id)
        .where(Appointment.created_at > state.last_seen_new_bookings_at)
        .where(Appointment.status.in_(["booked", "pending_approval"]))
    ).all()
    return NewBookingNotificationsOut(count=len(count))


@router.put("/dismiss-new-booking-notifications", status_code=204)
def dismiss_new_booking_notifications(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Doctor-only: mark new bookings as seen."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_doctor(user)

    state = session.get(DoctorNotificationState, user.id)
    if not state:
        state = DoctorNotificationState(doctor_id=user.id)
    state.last_seen_new_bookings_at = datetime.utcnow()
    session.add(state)
    session.commit()
    return None


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

    def _mins(hhmm: str) -> int:
        h, m = _parse_hhmm(hhmm)
        return h * 60 + m

    # Validate input times + prevent overlaps per day
    normalized_by_day: dict[int, list[tuple[int, int]]] = {d: [] for d in range(7)}
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
        normalized_by_day[slot.day_of_week].append((_mins(slot.start_time), _mins(slot.end_time)))

    for dow, windows in normalized_by_day.items():
        if len(windows) <= 1:
            continue
        windows_sorted = sorted(windows, key=lambda w: (w[0], w[1]))
        prev_start, prev_end = windows_sorted[0]
        for cur_start, cur_end in windows_sorted[1:]:
            if cur_start < prev_end:
                raise HTTPException(
                    status_code=400,
                    detail=f"Overlapping availability windows for day {dow}. Please remove overlaps.",
                )
            prev_start, prev_end = cur_start, cur_end

    # Block availability changes that would invalidate future appointments
    # (policy: safer to block than to orphan/cancel automatically)
    conflicts = _collect_future_appointment_conflicts_for_recurring_change(session, user.id, request.slots)

    if conflicts:
        # Returning structured details helps the UI show “why blocked”.
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Cannot save availability because it would invalidate existing future appointments.",
                "conflicts": [c.model_dump() for c in conflicts],
            },
        )

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


def _validate_custom_windows_no_overlap(windows: List[tuple[str, str, int]]) -> None:
    intervals: list[tuple[int, int]] = []
    for st, en, _dur in windows:
        try:
            a = _hhmm_to_mins(st)
            b = _hhmm_to_mins(en)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format in custom windows. Use HH:MM")
        if a >= b:
            raise HTTPException(status_code=400, detail="start_time must be before end_time for each custom window")
        intervals.append((a, b))
    intervals.sort(key=lambda x: (x[0], x[1]))
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i - 1][1]:
            raise HTTPException(
                status_code=400,
                detail="Overlapping custom hour windows for this date. Merge or remove overlaps.",
            )


@router.post("/exceptions", response_model=ScheduleExceptionOut, status_code=201)
def create_schedule_exception(
    body: ScheduleExceptionIn,
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Create a per-date schedule exception (block full day or custom hours for one date)."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_doctor(user)

    kind = body.kind.strip().lower()
    if kind not in ("blocked", "custom"):
        raise HTTPException(status_code=400, detail="kind must be 'blocked' or 'custom'")

    try:
        ex_date = datetime.strptime(body.exception_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exception_date. Use YYYY-MM-DD")

    if ex_date < date.today():
        raise HTTPException(status_code=400, detail="Exception date must be today or in the future.")

    if kind == "blocked":
        customs = session.exec(
            select(DoctorScheduleException)
            .where(DoctorScheduleException.doctor_id == user.id)
            .where(DoctorScheduleException.exception_date == body.exception_date)
            .where(DoctorScheduleException.kind == "custom")
        ).all()
        if customs:
            raise HTTPException(
                status_code=400,
                detail="Remove custom hour exceptions for this date before blocking the full day.",
            )

        appts = session.exec(
            select(Appointment)
            .where(Appointment.doctor_id == user.id)
            .where(Appointment.appointment_date == body.exception_date)
            .where(Appointment.status.in_(["booked", "pending_approval"]))
        ).all()
        if appts:
            conflicts: list[AvailabilityConflictOut] = []
            for appt in appts:
                if _is_past(appt.appointment_date, appt.start_time, appt.timezone):
                    continue
                patient_user = session.get(AuthUser, appt.patient_id)
                conflicts.append(
                    AvailabilityConflictOut(
                        appointment_id=appt.id,
                        appointment_date=appt.appointment_date,
                        start_time=appt.start_time,
                        end_time=appt.end_time,
                        patient_id=appt.patient_id,
                        patient_name=(patient_user.full_name if patient_user else "Unknown"),
                    )
                )
            if conflicts:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Cannot block this date because there are existing appointments.",
                        "conflicts": [c.model_dump() for c in conflicts],
                    },
                )

        row = DoctorScheduleException(
            doctor_id=user.id,
            exception_date=body.exception_date,
            kind="blocked",
            start_time=None,
            end_time=None,
            slot_duration_minutes=None,
            timezone=body.timezone,
            notes=body.notes,
        )
        session.add(row)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(status_code=409, detail="This date is already blocked.")
        session.refresh(row)
        return _schedule_exception_to_out(row)

    # custom
    blocked = session.exec(
        select(DoctorScheduleException)
        .where(DoctorScheduleException.doctor_id == user.id)
        .where(DoctorScheduleException.exception_date == body.exception_date)
        .where(DoctorScheduleException.kind == "blocked")
    ).first()
    if blocked:
        raise HTTPException(
            status_code=400,
            detail="Remove the blocked exception for this date before adding custom hours.",
        )

    if not body.start_time or not body.end_time:
        raise HTTPException(status_code=400, detail="start_time and end_time are required for custom exceptions")

    dur = body.slot_duration_minutes or 30
    if dur < 10 or dur > 120:
        raise HTTPException(status_code=400, detail="slot_duration_minutes must be 10–120")

    try:
        sh, sm = _parse_hhmm(body.start_time)
        eh, em = _parse_hhmm(body.end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
    if sh * 60 + sm >= eh * 60 + em:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    existing_custom = session.exec(
        select(DoctorScheduleException)
        .where(DoctorScheduleException.doctor_id == user.id)
        .where(DoctorScheduleException.exception_date == body.exception_date)
        .where(DoctorScheduleException.kind == "custom")
        .order_by(DoctorScheduleException.id)
    ).all()

    merged: List[tuple[str, str, int]] = [
        (c.start_time, c.end_time, c.slot_duration_minutes or 30)
        for c in existing_custom
        if c.start_time and c.end_time
    ]
    merged.append((body.start_time, body.end_time, dur))
    _validate_custom_windows_no_overlap(merged)

    appts = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == user.id)
        .where(Appointment.appointment_date == body.exception_date)
        .where(Appointment.status.in_(["booked", "pending_approval"]))
    ).all()
    conflicts2: list[AvailabilityConflictOut] = []
    for appt in appts:
        if _is_past(appt.appointment_date, appt.start_time, appt.timezone):
            continue
        try:
            ash, asm = _parse_hhmm(appt.start_time)
            aeh, aem = _parse_hhmm(appt.end_time)
        except ValueError:
            continue
        smins = ash * 60 + asm
        emins = aeh * 60 + aem
        if not _slot_times_fit_windows(smins, emins, merged):
            patient_user = session.get(AuthUser, appt.patient_id)
            conflicts2.append(
                AvailabilityConflictOut(
                    appointment_id=appt.id,
                    appointment_date=appt.appointment_date,
                    start_time=appt.start_time,
                    end_time=appt.end_time,
                    patient_id=appt.patient_id,
                    patient_name=(patient_user.full_name if patient_user else "Unknown"),
                )
            )

    if conflicts2:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Cannot add custom hours because existing appointments would fall outside the new windows.",
                "conflicts": [c.model_dump() for c in conflicts2],
            },
        )

    row = DoctorScheduleException(
        doctor_id=user.id,
        exception_date=body.exception_date,
        kind="custom",
        start_time=body.start_time,
        end_time=body.end_time,
        slot_duration_minutes=dur,
        timezone=body.timezone,
        notes=body.notes,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _schedule_exception_to_out(row)


@router.get("/exceptions/my", response_model=List[ScheduleExceptionOut])
def list_my_schedule_exceptions(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """List the authenticated doctor's schedule exceptions, optionally filtered by date range."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_doctor(user)

    q = select(DoctorScheduleException).where(DoctorScheduleException.doctor_id == user.id)
    if date_from:
        q = q.where(DoctorScheduleException.exception_date >= date_from)
    if date_to:
        q = q.where(DoctorScheduleException.exception_date <= date_to)
    q = q.order_by(DoctorScheduleException.exception_date, DoctorScheduleException.id)
    rows = session.exec(q).all()
    return [_schedule_exception_to_out(r) for r in rows]


@router.delete("/exceptions/{exception_id}", status_code=204)
def delete_schedule_exception(
    exception_id: int,
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session),
):
    """Delete a schedule exception owned by the authenticated doctor."""
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = _get_user_by_email(user_email, session)
    _require_doctor(user)

    row = session.get(DoctorScheduleException, exception_id)
    if not row or row.doctor_id != user.id:
        raise HTTPException(status_code=404, detail="Exception not found")

    session.delete(row)
    session.commit()
    return None


@router.get("/doctors/{doctor_id}/exceptions", response_model=List[ScheduleExceptionOut])
def list_doctor_schedule_exceptions(
    doctor_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """List schedule exceptions for a doctor (used by patient booking UI)."""
    doctor = session.get(AuthUser, doctor_id)
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")

    q = select(DoctorScheduleException).where(DoctorScheduleException.doctor_id == doctor_id)
    if date_from:
        q = q.where(DoctorScheduleException.exception_date >= date_from)
    if date_to:
        q = q.where(DoctorScheduleException.exception_date <= date_to)
    q = q.order_by(DoctorScheduleException.exception_date, DoctorScheduleException.id)
    rows = session.exec(q).all()
    return [_schedule_exception_to_out(r) for r in rows]


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
    date: Optional[str] = None,  # ?date=YYYY-MM-DD (kept name for backwards compat)
    session: Session = Depends(get_session),
):
    """
    Return bookable time slots for a doctor on a specific date.

    Pass `?date=YYYY-MM-DD` as a query parameter.
    """
    # NOTE: param name `date` shadows datetime.date class in this scope.
    # Keep query param name stable but avoid using it as an identifier.
    target_date_str = date
    # validate date
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if target_date < datetime.today().date():
        return []

    doctor = session.get(AuthUser, doctor_id)
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")

    wins = _effective_windows_for_date(session, doctor_id, target_date_str, recurring_slots_override=None)
    if wins is None:
        return []
    if not wins:
        return []

    # Generate all possible slots from effective windows (recurring or custom exception)
    all_slots: List[tuple[str, str]] = []
    for st, en, dur in wins:
        all_slots.extend(_generate_slots(st, en, dur))

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

    # Validate date + booking horizon
    try:
        appt_date = datetime.strptime(request.appointment_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    max_bookable = date.today() + timedelta(days=BOOKING_HORIZON_DAYS)
    if appt_date > max_bookable:
        raise HTTPException(
            status_code=400,
            detail=f"Appointments can only be booked within the next {BOOKING_HORIZON_DAYS} days.",
        )

    # Validate times
    try:
        sh, sm = _parse_hhmm(request.start_time)
        eh, em = _parse_hhmm(request.end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
    if sh * 60 + sm >= eh * 60 + em:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    _validate_slot_against_availability(
        session,
        request.doctor_id,
        request.appointment_date,
        request.start_time,
        request.end_time,
    )

    if _is_past(request.appointment_date, request.start_time, request.timezone):
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past.")

    # Pre-check (DB unique index is the authoritative guard against races)
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

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot just got booked, please choose another time.",
        )
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

    if _is_past(appt.appointment_date, appt.start_time, appt.timezone):
        raise HTTPException(status_code=400, detail="Cannot cancel a past appointment.")

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

    if _is_past(appt.appointment_date, appt.start_time, appt.timezone):
        raise HTTPException(status_code=400, detail="Cannot reschedule a past appointment.")

    # Validate new times + booking horizon
    try:
        new_appt_date = datetime.strptime(request.appointment_date, "%Y-%m-%d").date()
        sh, sm = _parse_hhmm(request.start_time)
        eh, em = _parse_hhmm(request.end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format")

    max_bookable = date.today() + timedelta(days=BOOKING_HORIZON_DAYS)
    if new_appt_date > max_bookable:
        raise HTTPException(
            status_code=400,
            detail=f"Appointments can only be rescheduled within the next {BOOKING_HORIZON_DAYS} days.",
        )

    if sh * 60 + sm >= eh * 60 + em:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    _validate_slot_against_availability(
        session,
        appt.doctor_id,
        request.appointment_date,
        request.start_time,
        request.end_time,
    )

    if _is_past(request.appointment_date, request.start_time, request.timezone):
        raise HTTPException(status_code=400, detail="Cannot reschedule to a time in the past.")

    # Check no existing booking at the new slot (same statuses as slot listing)
    conflict = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == appt.doctor_id)
        .where(Appointment.appointment_date == request.appointment_date)
        .where(Appointment.start_time == request.start_time)
        .where(Appointment.status.in_(["booked", "pending_approval"]))
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
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot just got booked, please choose another time.",
        )
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
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot approve: the linked appointment conflicts with an existing booking for this slot.",
        )
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

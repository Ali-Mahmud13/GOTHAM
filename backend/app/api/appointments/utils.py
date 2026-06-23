from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.appointments import (
    Appointment,
    DoctorAvailability,
    DoctorScheduleException,
)
from app.models.auth import AuthUser
from app.models.patient import Patient

from .schemas import AvailabilityConflictOut, AvailabilitySlotIn, AppointmentOut

BOOKING_HORIZON_DAYS = 14
MIN_BOOKING_LEAD_HOURS = 2
ACTIVE_APPOINTMENT_STATUSES = ("booked", "pending_approval")


def _require_doctor(user: AuthUser) -> None:
    if user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can perform this action")


def _require_patient(user: AuthUser) -> None:
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can perform this action")


def _parse_hhmm(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(f"Expected HH:MM, got '{value}'")
    hour, minute = int(parts[0]), int(parts[1])
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError(f"Invalid time '{value}'")
    return hour, minute


def _hhmm_to_mins(value: str) -> int:
    hour, minute = _parse_hhmm(value)
    return hour * 60 + minute


def _generate_slots(start_hhmm: str, end_hhmm: str, duration_minutes: int) -> List[tuple[str, str]]:
    if duration_minutes <= 0:
        raise ValueError("Slot duration must be positive")
    start = _hhmm_to_mins(start_hhmm)
    end = _hhmm_to_mins(end_hhmm)
    if start >= end:
        raise ValueError("Start must be before end")
    slots: list[tuple[str, str]] = []
    current = start
    while current + duration_minutes <= end:
        nxt = current + duration_minutes
        slots.append(
            (
                f"{current // 60:02d}:{current % 60:02d}",
                f"{nxt // 60:02d}:{nxt % 60:02d}",
            )
        )
        current = nxt
    return slots


def _safe_tz(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def _local_slot_to_utc(
    appointment_date: str,
    start_time: str,
    end_time: str,
    tz_name: str,
) -> tuple[datetime, datetime]:
    zone = _safe_tz(tz_name)
    start_naive = datetime.strptime(
        f"{appointment_date} {start_time}", "%Y-%m-%d %H:%M"
    )
    end_naive = datetime.strptime(
        f"{appointment_date} {end_time}", "%Y-%m-%d %H:%M"
    )
    start_local = start_naive.replace(tzinfo=zone)
    end_local = end_naive.replace(tzinfo=zone)
    if start_local.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != start_naive:
        raise ValueError("Appointment start falls in a daylight-saving time gap")
    if end_local.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != end_naive:
        raise ValueError("Appointment end falls in a daylight-saving time gap")
    if end_local <= start_local:
        raise ValueError("Appointment end must be after start")
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _appointment_utc_bounds(appt: Appointment) -> tuple[datetime, datetime]:
    if appt.start_at_utc and appt.end_at_utc:
        return _as_aware_utc(appt.start_at_utc), _as_aware_utc(appt.end_at_utc)
    return _local_slot_to_utc(
        appt.appointment_date,
        appt.start_time,
        appt.end_time,
        appt.schedule_timezone or appt.timezone,
    )


def _appointment_is_elapsed(appt: Appointment, now: Optional[datetime] = None) -> bool:
    _, end_at = _appointment_utc_bounds(appt)
    return end_at <= (now or datetime.now(timezone.utc))


def _appointment_is_future(appt: Appointment, now: Optional[datetime] = None) -> bool:
    start_at, _ = _appointment_utc_bounds(appt)
    return start_at > (now or datetime.now(timezone.utc))


def _reconcile_elapsed_appointments(
    session: Session,
    appointments: List[Appointment],
    now: Optional[datetime] = None,
) -> None:
    changed = False
    for appt in appointments:
        if appt.status == "booked" and _appointment_is_elapsed(appt, now):
            appt.status = "awaiting_outcome"
            appt.updated_at = datetime.utcnow()
            session.add(appt)
            changed = True
        elif appt.status == "pending_approval" and _appointment_is_elapsed(appt, now):
            appt.status = "cancelled"
            appt.cancellation_reason = "registration_request_expired"
            appt.updated_at = datetime.utcnow()
            session.add(appt)
            changed = True
    if changed:
        session.commit()


def _is_past(appointment_date: str, start_time: str, tz_name: str) -> bool:
    zone = _safe_tz(tz_name)
    local = datetime.strptime(
        f"{appointment_date} {start_time}", "%Y-%m-%d %H:%M"
    ).replace(tzinfo=zone)
    return local.astimezone(timezone.utc) < datetime.now(timezone.utc)


def _is_within_lead_time(appointment_date: str, start_time: str, tz_name: str) -> bool:
    zone = _safe_tz(tz_name)
    start_at = datetime.strptime(
        f"{appointment_date} {start_time}", "%Y-%m-%d %H:%M"
    ).replace(tzinfo=zone).astimezone(timezone.utc)
    return start_at < datetime.now(timezone.utc) + timedelta(hours=MIN_BOOKING_LEAD_HOURS)


def _validate_booking_window(start_at_utc: datetime) -> None:
    now = datetime.now(timezone.utc)
    if start_at_utc < now:
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past.")
    if start_at_utc < now + timedelta(hours=MIN_BOOKING_LEAD_HOURS):
        raise HTTPException(
            status_code=400,
            detail=f"Appointments must be booked at least {MIN_BOOKING_LEAD_HOURS} hour(s) in advance.",
        )
    if start_at_utc > now + timedelta(days=BOOKING_HORIZON_DAYS):
        raise HTTPException(
            status_code=400,
            detail=f"Appointments may only be booked {BOOKING_HORIZON_DAYS} days in advance.",
        )


def _subtract_blocked_times(
    windows: List[tuple[str, str, int]],
    blocks: List[DoctorScheduleException],
) -> List[tuple[str, str, int]]:
    blocked_ranges: list[tuple[int, int]] = []
    for block in blocks:
        if not block.start_time or not block.end_time:
            continue
        blocked_ranges.append(
            (_hhmm_to_mins(block.start_time), _hhmm_to_mins(block.end_time))
        )

    result: list[tuple[str, str, int]] = []
    for start_text, end_text, duration in windows:
        intervals = [(_hhmm_to_mins(start_text), _hhmm_to_mins(end_text))]
        for blocked_start, blocked_end in blocked_ranges:
            next_intervals = []
            for current_start, current_end in intervals:
                if blocked_end <= current_start or blocked_start >= current_end:
                    next_intervals.append((current_start, current_end))
                    continue
                if current_start < blocked_start:
                    next_intervals.append((current_start, blocked_start))
                if blocked_end < current_end:
                    next_intervals.append((blocked_end, current_end))
            intervals = next_intervals
        for current_start, current_end in intervals:
            if current_end - current_start >= duration:
                result.append(
                    (
                        f"{current_start // 60:02d}:{current_start % 60:02d}",
                        f"{current_end // 60:02d}:{current_end % 60:02d}",
                        duration,
                    )
                )
    return result


def _effective_windows_for_date(
    session: Session,
    doctor_id: int,
    target_date_str: str,
    recurring_slots_override: Optional[List[AvailabilitySlotIn]] = None,
) -> Optional[List[tuple[str, str, int]]]:
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        return []

    full_day_block = session.exec(
        select(DoctorScheduleException)
        .where(DoctorScheduleException.doctor_id == doctor_id)
        .where(DoctorScheduleException.exception_date == target_date_str)
        .where(DoctorScheduleException.kind == "blocked")
    ).first()
    if full_day_block:
        return None

    custom_rows = session.exec(
        select(DoctorScheduleException)
        .where(DoctorScheduleException.doctor_id == doctor_id)
        .where(DoctorScheduleException.exception_date == target_date_str)
        .where(DoctorScheduleException.kind == "custom")
        .order_by(DoctorScheduleException.start_time)
    ).all()
    if custom_rows:
        windows = [
            (row.start_time, row.end_time, row.slot_duration_minutes or 30)
            for row in custom_rows
            if row.start_time and row.end_time
        ]
    elif recurring_slots_override is not None:
        windows = [
            (slot.start_time, slot.end_time, slot.slot_duration_minutes)
            for slot in recurring_slots_override
            if slot.day_of_week == target_date.weekday()
        ]
    else:
        availability = session.exec(
            select(DoctorAvailability)
            .where(DoctorAvailability.doctor_id == doctor_id)
            .where(DoctorAvailability.day_of_week == target_date.weekday())
            .where(DoctorAvailability.is_active == True)
        ).all()
        windows = [
            (row.start_time, row.end_time, row.slot_duration_minutes)
            for row in availability
        ]

    blocked_intervals = session.exec(
        select(DoctorScheduleException)
        .where(DoctorScheduleException.doctor_id == doctor_id)
        .where(DoctorScheduleException.exception_date == target_date_str)
        .where(DoctorScheduleException.kind == "blocked_interval")
    ).all()
    return _subtract_blocked_times(windows, blocked_intervals) if blocked_intervals else windows


def _schedule_timezone_for_date(
    session: Session,
    doctor_id: int,
    target_date_str: str,
) -> str:
    custom = session.exec(
        select(DoctorScheduleException)
        .where(DoctorScheduleException.doctor_id == doctor_id)
        .where(DoctorScheduleException.exception_date == target_date_str)
        .where(DoctorScheduleException.kind == "custom")
    ).first()
    if custom:
        return custom.timezone
    try:
        weekday = datetime.strptime(target_date_str, "%Y-%m-%d").date().weekday()
    except ValueError:
        return "UTC"
    availability = session.exec(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == doctor_id)
        .where(DoctorAvailability.day_of_week == weekday)
        .where(DoctorAvailability.is_active == True)
    ).first()
    return availability.timezone if availability else "UTC"


def _slot_times_fit_windows(
    start_minutes: int,
    end_minutes: int,
    windows: List[tuple[str, str, int]],
) -> bool:
    for start_text, end_text, duration in windows:
        window_start = _hhmm_to_mins(start_text)
        window_end = _hhmm_to_mins(end_text)
        if (
            duration > 0
            and window_start <= start_minutes
            and end_minutes <= window_end
            and (start_minutes - window_start) % duration == 0
            and end_minutes - start_minutes == duration
        ):
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
        datetime.strptime(appointment_date, "%Y-%m-%d")
        start_minutes = _hhmm_to_mins(start_time)
        end_minutes = _hhmm_to_mins(end_time)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if start_minutes >= end_minutes:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")
    windows = _effective_windows_for_date(session, doctor_id, appointment_date)
    if windows is None:
        raise HTTPException(status_code=400, detail="The doctor is not available on this date.")
    if not windows:
        raise HTTPException(status_code=400, detail="No working hours are configured for this date.")
    if not _slot_times_fit_windows(start_minutes, end_minutes, windows):
        raise HTTPException(
            status_code=400,
            detail="The selected time is outside the doctor's availability or slot grid.",
        )


def _appointment_matches_effective_schedule(
    session: Session,
    doctor_id: int,
    appt: Appointment,
    *,
    recurring_slots_override: Optional[List[AvailabilitySlotIn]] = None,
) -> bool:
    if not _appointment_is_future(appt):
        return True
    windows = _effective_windows_for_date(
        session,
        doctor_id,
        appt.appointment_date,
        recurring_slots_override=recurring_slots_override,
    )
    if not windows:
        return False
    return _slot_times_fit_windows(
        _hhmm_to_mins(appt.start_time),
        _hhmm_to_mins(appt.end_time),
        windows,
    )


def _conflict_out(session: Session, appt: Appointment) -> AvailabilityConflictOut:
    patient_user = session.get(AuthUser, appt.patient_id)
    return AvailabilityConflictOut(
        appointment_id=appt.id,
        appointment_date=appt.appointment_date,
        start_time=appt.start_time,
        end_time=appt.end_time,
        patient_id=appt.patient_id,
        patient_name=patient_user.full_name if patient_user else "Unknown",
    )


def _collect_future_appointment_conflicts_for_recurring_change(
    session: Session,
    doctor_id: int,
    recurring_slots: List[AvailabilitySlotIn],
) -> list[AvailabilityConflictOut]:
    appointments = session.exec(
        select(Appointment)
        .where(Appointment.doctor_id == doctor_id)
        .where(Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES))
    ).all()
    return [
        _conflict_out(session, appt)
        for appt in appointments
        if _appointment_is_future(appt)
        and not _appointment_matches_effective_schedule(
            session,
            doctor_id,
            appt,
            recurring_slots_override=recurring_slots,
        )
    ]


def _validate_custom_windows_no_overlap(windows: List[tuple[int, int]]) -> None:
    sorted_windows = sorted(windows)
    for previous, current in zip(sorted_windows, sorted_windows[1:]):
        if current[0] < previous[1]:
            raise HTTPException(status_code=400, detail="Availability windows cannot overlap.")


def _appointment_out(appt: Appointment, session: Session) -> AppointmentOut:
    doctor = session.get(AuthUser, appt.doctor_id)
    patient_user = session.get(AuthUser, appt.patient_id)
    is_registered = False
    if patient_user and patient_user.patient_id:
        patient = session.get(Patient, patient_user.patient_id)
        is_registered = bool(patient and patient.doctor_id == appt.doctor_id)
    start_at_utc, end_at_utc = _appointment_utc_bounds(appt)
    return AppointmentOut(
        id=appt.id,
        doctor_id=appt.doctor_id,
        doctor_name=doctor.full_name if doctor else "Unknown",
        patient_id=appt.patient_id,
        patient_name=patient_user.full_name if patient_user else "Unknown",
        appointment_date=appt.appointment_date,
        start_time=appt.start_time,
        end_time=appt.end_time,
        timezone=appt.timezone,
        schedule_timezone=appt.schedule_timezone or appt.timezone,
        start_at_utc=start_at_utc,
        end_at_utc=end_at_utc,
        status=appt.status,
        notes=appt.notes,
        created_at=appt.created_at,
        is_registered=is_registered,
        rescheduled_by=appt.rescheduled_by,
        cancelled_by=appt.cancelled_by,
        cancellation_reason=appt.cancellation_reason,
        outcome_recorded_at=appt.outcome_recorded_at,
        outcome_recorded_by=appt.outcome_recorded_by,
    )

from datetime import datetime, date, timedelta
from typing import List, Optional, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.auth import AuthUser
from app.models.appointments import Appointment, DoctorAvailability, DoctorScheduleException, RegistrationRequest
from app.models.patient import Patient
from .schemas import AvailabilitySlotIn, AvailabilityConflictOut, AppointmentOut

BOOKING_HORIZON_DAYS = 14

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


def _validate_custom_windows_no_overlap(windows: List[tuple[int, int]]) -> None:
    if len(windows) <= 1:
        return
    sorted_wins = sorted(windows, key=lambda w: (w[0], w[1]))
    prev_start, prev_end = sorted_wins[0]
    for cur_start, cur_end in sorted_wins[1:]:
        if cur_start < prev_end:
            raise HTTPException(
                status_code=400,
                detail="Overlapping custom availability windows detected. Please remove overlaps.",
            )
        prev_start, prev_end = cur_start, cur_end


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

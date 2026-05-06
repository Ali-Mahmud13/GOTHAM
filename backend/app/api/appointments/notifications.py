from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, or_

from app.db.session import get_session
from app.core.security import get_current_user_compat
from app.models.auth import AuthUser
from app.models.appointments import Appointment, DoctorNotificationState

from .schemas import AppointmentOut, NewBookingNotificationsOut
from .utils import _appointment_out, _require_doctor

router = APIRouter()

@router.get("/reschedule-notifications", response_model=List[AppointmentOut])
def get_reschedule_notifications(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return rescheduled appointments for the current user."""
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
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Clear all reschedule notifications."""
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
    for a in appts:
        a.rescheduled_by = None
        session.add(a)
    session.commit()


@router.get("/cancel-notifications", response_model=List[AppointmentOut])
def get_cancel_notifications(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return cancelled appointments for the current user."""
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
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Clear all cancel notifications."""
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
    for a in appts:
        a.cancelled_by = None
        session.add(a)
    session.commit()


@router.get("/new-booking-notifications", response_model=NewBookingNotificationsOut)
def get_new_booking_notifications(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return count of new bookings since doctor last cleared them."""
    _require_doctor(user)
    state = session.exec(
        select(DoctorNotificationState).where(DoctorNotificationState.doctor_id == user.id)
    ).first()
    
    since = state.last_seen_new_bookings_at if state else datetime(2000, 1, 1)

    # We count:
    # 1. Any appointment in 'pending_approval' status (these ALWAYS need attention until processed)
    # 2. Any 'booked' appointment created after the last check
    query = (
        select(Appointment)
        .where(Appointment.doctor_id == user.id)
        .where(
            or_(
                Appointment.status == "pending_approval",
                (Appointment.status == "booked") & (Appointment.created_at > since)
            )
        )
    )
    count = session.exec(query).all()
    return NewBookingNotificationsOut(count=len(count))


@router.put("/dismiss-new-booking-notifications", status_code=204)
def dismiss_new_booking_notifications(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Update last_seen_new_bookings_at for the doctor."""
    _require_doctor(user)
    state = session.exec(
        select(DoctorNotificationState).where(DoctorNotificationState.doctor_id == user.id)
    ).first()
    if not state:
        state = DoctorNotificationState(doctor_id=user.id)
    
    state.last_seen_new_bookings_at = datetime.utcnow()
    session.add(state)
    session.commit()

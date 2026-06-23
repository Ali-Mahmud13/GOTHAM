"""Appointment and Doctor Availability models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Index, text
from sqlmodel import Field, SQLModel


class RegistrationRequest(SQLModel, table=True):
    """A patient's request to register under a doctor (with data-access grant)."""

    __tablename__ = "registration_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="auth_users.id", index=True)
    doctor_id: int = Field(foreign_key="auth_users.id", index=True)
    # The pending appointment linked to this request (nullable for standalone requests)
    appointment_id: Optional[int] = Field(default=None, foreign_key="appointments.id")
    # pending | approved | declined
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DoctorAvailability(SQLModel, table=True):
    """Recurring weekly availability slots for doctors."""

    __tablename__ = "doctor_availability"

    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="auth_users.id", index=True)
    # 0=Monday … 6=Sunday (ISO weekday - 1)
    day_of_week: int = Field(description="0=Monday, 1=Tuesday, ..., 6=Sunday")
    # 24-hour "HH:MM" strings stored in the doctor's stated timezone
    start_time: str = Field(description="Start time HH:MM")
    end_time: str = Field(description="End time HH:MM")
    # IANA timezone name, e.g. "Asia/Karachi"
    timezone: str = Field(default="UTC")
    slot_duration_minutes: int = Field(default=30, description="Duration of each bookable slot in minutes")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DoctorScheduleException(SQLModel, table=True):
    """Per-date replacement hours or blocked interval/day."""

    __tablename__ = "doctor_schedule_exceptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="auth_users.id", index=True)
    exception_date: str = Field(index=True, description="YYYY-MM-DD")
    kind: str = Field(description="'blocked', 'blocked_interval', or 'custom'")
    start_time: Optional[str] = Field(default=None, description="HH:MM for timed exceptions")
    end_time: Optional[str] = Field(default=None, description="HH:MM for timed exceptions")
    slot_duration_minutes: Optional[int] = Field(default=None, description="Slot length for custom hours")
    timezone: str = Field(default="UTC")
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DoctorNotificationState(SQLModel, table=True):
    """Lightweight per-doctor notification read state."""

    __tablename__ = "doctor_notification_state"

    doctor_id: int = Field(foreign_key="auth_users.id", primary_key=True)
    last_seen_new_bookings_at: datetime = Field(default_factory=datetime.utcnow)


class Appointment(SQLModel, table=True):
    """A booked appointment between a doctor and a patient."""

    __tablename__ = "appointments"
    __table_args__ = (
        Index(
            "uq_appt_active_slot",
            "doctor_id",
            "appointment_date",
            "start_time",
            unique=True,
            postgresql_where=text("status IN ('booked', 'pending_approval')"),
            sqlite_where=text("status IN ('booked', 'pending_approval')"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="auth_users.id", index=True)
    patient_id: int = Field(foreign_key="auth_users.id", index=True)
    # Store date as ISO string "YYYY-MM-DD" for simplicity
    appointment_date: str = Field(index=True, description="Date YYYY-MM-DD")
    start_time: str = Field(description="Start time HH:MM")
    end_time: str = Field(description="End time HH:MM")
    # Legacy local fields remain during the UTC migration.
    timezone: str = Field(default="UTC")
    schedule_timezone: str = Field(default="UTC")
    start_at_utc: Optional[datetime] = Field(default=None, index=True)
    end_at_utc: Optional[datetime] = Field(default=None, index=True)
    # pending_approval is retained only for legacy linked registration requests.
    # booked | pending_approval | awaiting_outcome | completed | no_show | cancelled
    status: str = Field(default="booked")
    notes: Optional[str] = Field(default=None)
    # Set to "doctor" or "patient" when that party reschedules; cleared when the other party views
    rescheduled_by: Optional[str] = Field(default=None)
    # Set to "doctor" or "patient" when that party cancels; cleared when the other party views
    cancelled_by: Optional[str] = Field(default=None)
    cancellation_reason: Optional[str] = Field(default=None)
    outcome_recorded_at: Optional[datetime] = Field(default=None)
    outcome_recorded_by: Optional[int] = Field(default=None, foreign_key="auth_users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

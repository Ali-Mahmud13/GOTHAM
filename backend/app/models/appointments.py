"""Appointment and Doctor Availability models."""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


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


class Appointment(SQLModel, table=True):
    """A booked appointment between a doctor and a patient."""

    __tablename__ = "appointments"

    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="auth_users.id", index=True)
    patient_id: int = Field(foreign_key="auth_users.id", index=True)
    # Store date as ISO string "YYYY-MM-DD" for simplicity
    appointment_date: str = Field(index=True, description="Date YYYY-MM-DD")
    start_time: str = Field(description="Start time HH:MM")
    end_time: str = Field(description="End time HH:MM")
    # IANA timezone name used when the slot was displayed to the patient
    timezone: str = Field(default="UTC")
    # booked | cancelled | completed | rescheduled
    status: str = Field(default="booked")
    notes: Optional[str] = Field(default=None)
    # Set to "doctor" or "patient" when that party reschedules; cleared when the other party views
    rescheduled_by: Optional[str] = Field(default=None)
    # Set to "doctor" or "patient" when that party cancels; cleared when the other party views
    cancelled_by: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

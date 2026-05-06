from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

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


class RegisteredPatientOut(BaseModel):
    patient_auth_id: int
    patient_name: str
    patient_email: str
    patient_identifier: str

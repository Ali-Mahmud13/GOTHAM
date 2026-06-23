from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator


def _validate_hhmm(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueError("Time must use 24-hour HH:MM format") from exc
    return parsed.strftime("%H:%M")


def _validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("Timezone must be a valid IANA timezone") from exc
    return value


def _validate_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError("Date must use YYYY-MM-DD format") from exc


class AvailabilitySlotIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str
    end_time: str
    timezone: str = "UTC"
    slot_duration_minutes: int = Field(default=30, ge=5, le=480)

    _start = field_validator("start_time")(_validate_hhmm)
    _end = field_validator("end_time")(_validate_hhmm)
    _timezone = field_validator("timezone")(_validate_timezone)

    @model_validator(mode="after")
    def validate_window(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class AvailabilitySlotOut(BaseModel):
    id: int
    day_of_week: int
    start_time: str
    end_time: str
    timezone: str
    slot_duration_minutes: int
    is_active: bool


class SetAvailabilityRequest(BaseModel):
    slots: List[AvailabilitySlotIn]

    @model_validator(mode="after")
    def validate_single_timezone(self):
        timezones = {slot.timezone for slot in self.slots}
        if len(timezones) > 1:
            raise ValueError("All recurring availability must use one timezone")
        return self


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
    specialty: Optional[str] = None
    clinic_name: Optional[str] = None
    bio: Optional[str] = None


class PatientRegistrationRequestOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    doctor_name: str
    doctor_email: str
    appointment_id: Optional[int]
    appointment_date: Optional[str]
    appointment_start_time: Optional[str]
    status: str
    created_at: datetime


class TimeSlotOut(BaseModel):
    start_time: str
    end_time: str
    available: bool
    schedule_timezone: str
    start_at_utc: datetime
    end_at_utc: datetime


class BookingRequest(BaseModel):
    doctor_id: int
    appointment_date: str
    start_time: str
    end_time: str
    notes: Optional[str] = None

    _date = field_validator("appointment_date")(_validate_date)
    _start = field_validator("start_time")(_validate_hhmm)
    _end = field_validator("end_time")(_validate_hhmm)

    @model_validator(mode="after")
    def validate_window(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


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
    schedule_timezone: str
    start_at_utc: datetime
    end_at_utc: datetime
    status: str
    notes: Optional[str]
    created_at: datetime
    is_registered: bool = False
    rescheduled_by: Optional[str] = None
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    outcome_recorded_at: Optional[datetime] = None
    outcome_recorded_by: Optional[int] = None


class RescheduleRequest(BaseModel):
    appointment_date: str
    start_time: str
    end_time: str

    _date = field_validator("appointment_date")(_validate_date)
    _start = field_validator("start_time")(_validate_hhmm)
    _end = field_validator("end_time")(_validate_hhmm)

    @model_validator(mode="after")
    def validate_window(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class AppointmentOutcomeRequest(BaseModel):
    outcome: str

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"completed", "no_show"}:
            raise ValueError("outcome must be completed or no_show")
        return normalized


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


class StandaloneRegistrationRequest(BaseModel):
    doctor_id: int


class ScheduleExceptionIn(BaseModel):
    exception_date: str
    kind: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    slot_duration_minutes: Optional[int] = Field(default=30, ge=5, le=480)
    timezone: str = "UTC"
    notes: Optional[str] = None

    _date = field_validator("exception_date")(_validate_date)
    _timezone = field_validator("timezone")(_validate_timezone)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_optional_time(cls, value: Optional[str]) -> Optional[str]:
        return _validate_hhmm(value) if value is not None else None

    @model_validator(mode="after")
    def validate_exception(self):
        self.kind = self.kind.strip().lower()
        if self.kind not in {"blocked", "blocked_interval", "custom"}:
            raise ValueError("kind must be blocked, blocked_interval, or custom")
        if self.kind in {"blocked_interval", "custom"}:
            if not self.start_time or not self.end_time:
                raise ValueError("start_time and end_time are required")
            if self.start_time >= self.end_time:
                raise ValueError("start_time must be before end_time")
        return self


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


class ScheduleExceptionCreatedOut(BaseModel):
    exception: ScheduleExceptionOut
    impacted_appointments: List[AvailabilityConflictOut] = []


class BookingConfigOut(BaseModel):
    booking_horizon_days: int
    min_booking_lead_hours: int = 2


class NewBookingNotificationsOut(BaseModel):
    count: int


class RegisteredPatientOut(BaseModel):
    patient_auth_id: int
    patient_name: str
    patient_email: str
    patient_identifier: str

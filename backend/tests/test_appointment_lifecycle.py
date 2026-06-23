from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

from app.api.appointments.availability import (
    create_schedule_exception,
    delete_schedule_exception,
)
from app.api.appointments.booking import (
    book_appointment,
    get_my_appointments,
    record_appointment_outcome,
)
from app.api.appointments.registration import (
    approve_registration_request,
    patient_unregister,
)
from app.api.appointments.schemas import (
    AppointmentOutcomeRequest,
    AvailabilitySlotIn,
    BookingRequest,
    ScheduleExceptionIn,
)
from app.api.appointments.utils import (
    _effective_windows_for_date,
    _local_slot_to_utc,
)
from app.api.auth import CloseAccountRequest, close_patient_account
from app.core.security import create_access_token, get_current_user
from app.models import (
    Appointment,
    AuthUser,
    DoctorAvailability,
    DoctorScheduleException,
    Patient,
    RegistrationRequest,
)


def _memory_session() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _doctor(user_id: int, timezone_name: str = "Asia/Karachi") -> AuthUser:
    return AuthUser(
        id=user_id,
        email=f"doctor-{user_id}@example.com",
        password_hash="test",
        role="doctor",
        full_name=f"Doctor {user_id}",
        is_active=True,
        verification_status="verified",
    )


def _patient_user(user_id: int, patient_id: int) -> AuthUser:
    return AuthUser(
        id=user_id,
        email=f"patient-{user_id}@example.com",
        password_hash="test",
        role="patient",
        full_name=f"Patient {user_id}",
        patient_id=patient_id,
        is_active=True,
    )


def _future_local_date(timezone_name: str = "Asia/Karachi", days: int = 3) -> str:
    return (datetime.now(ZoneInfo(timezone_name)) + timedelta(days=days)).date().isoformat()


def _add_availability(
    session: Session,
    doctor_id: int,
    local_date: str,
    timezone_name: str = "Asia/Karachi",
) -> None:
    weekday = datetime.strptime(local_date, "%Y-%m-%d").date().weekday()
    session.add(
        DoctorAvailability(
            doctor_id=doctor_id,
            day_of_week=weekday,
            start_time="09:00",
            end_time="12:00",
            timezone=timezone_name,
            slot_duration_minutes=30,
        )
    )


def test_availability_schema_rejects_invalid_values():
    with pytest.raises(ValueError):
        AvailabilitySlotIn(
            day_of_week=7,
            start_time="09:00",
            end_time="10:00",
            slot_duration_minutes=30,
        )
    with pytest.raises(ValueError):
        AvailabilitySlotIn(
            day_of_week=1,
            start_time="09:00",
            end_time="10:00",
            slot_duration_minutes=0,
        )
    with pytest.raises(ValueError):
        AvailabilitySlotIn(
            day_of_week=1,
            start_time="25:00",
            end_time="26:00",
            slot_duration_minutes=30,
        )


def test_booking_requires_assigned_doctor_and_uses_schedule_timezone():
    with _memory_session() as session:
        doctor = _doctor(10)
        patient = Patient(
            patient_identifier="P900",
            name="Booking Patient",
            age=30,
            contact_number="000",
        )
        session.add(doctor)
        session.add(patient)
        session.flush()
        user = _patient_user(20, patient.id)
        session.add(user)
        local_date = _future_local_date()
        _add_availability(session, doctor.id, local_date)
        session.commit()

        request = BookingRequest(
            doctor_id=doctor.id,
            appointment_date=local_date,
            start_time="09:00",
            end_time="09:30",
        )
        with pytest.raises(HTTPException) as error:
            book_appointment(request, user, session)
        assert error.value.status_code == 403

        patient.doctor_id = doctor.id
        session.add(patient)
        session.commit()
        result = book_appointment(request, user, session)
        expected_start, _ = _local_slot_to_utc(
            local_date, "09:00", "09:30", "Asia/Karachi"
        )
        assert result.schedule_timezone == "Asia/Karachi"
        assert result.start_at_utc == expected_start
        assert result.status == "booked"


def test_elapsed_appointment_requires_doctor_outcome():
    with _memory_session() as session:
        doctor = _doctor(11)
        patient = Patient(
            patient_identifier="P901",
            name="Outcome Patient",
            age=31,
            contact_number="000",
            doctor_id=doctor.id,
        )
        session.add(doctor)
        session.add(patient)
        session.flush()
        patient_user = _patient_user(21, patient.id)
        session.add(patient_user)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        appointment = Appointment(
            doctor_id=doctor.id,
            patient_id=patient_user.id,
            appointment_date=yesterday.date().isoformat(),
            start_time="09:00",
            end_time="09:30",
            timezone="UTC",
            schedule_timezone="UTC",
            start_at_utc=(yesterday - timedelta(minutes=30)).replace(tzinfo=None),
            end_at_utc=yesterday.replace(tzinfo=None),
            status="booked",
        )
        session.add(appointment)
        session.commit()

        history = get_my_appointments(doctor, session)
        assert history[0].status == "awaiting_outcome"

        completed = record_appointment_outcome(
            appointment.id,
            AppointmentOutcomeRequest(outcome="completed"),
            doctor,
            session,
        )
        assert completed.status == "completed"
        assert completed.outcome_recorded_by == doctor.id


def test_unregister_cancels_future_appointment_but_keeps_login_active():
    with _memory_session() as session:
        doctor = _doctor(12)
        patient = Patient(
            patient_identifier="P902",
            name="Unregister Patient",
            age=32,
            contact_number="000",
            doctor_id=doctor.id,
        )
        session.add(doctor)
        session.add(patient)
        session.flush()
        user = _patient_user(22, patient.id)
        session.add(user)
        start = datetime.now(timezone.utc) + timedelta(days=2)
        appointment = Appointment(
            doctor_id=doctor.id,
            patient_id=user.id,
            appointment_date=start.date().isoformat(),
            start_time="09:00",
            end_time="09:30",
            timezone="UTC",
            schedule_timezone="UTC",
            start_at_utc=start.replace(tzinfo=None),
            end_at_utc=(start + timedelta(minutes=30)).replace(tzinfo=None),
            status="booked",
        )
        session.add(appointment)
        session.commit()

        patient_unregister(user, session)
        session.refresh(patient)
        session.refresh(user)
        session.refresh(appointment)
        assert patient.doctor_id is None
        assert user.is_active is True
        assert appointment.status == "cancelled"
        assert appointment.cancellation_reason == "patient_unregistered"


def test_approval_closes_competing_registration_requests():
    with _memory_session() as session:
        first_doctor = _doctor(13)
        second_doctor = _doctor(14)
        patient = Patient(
            patient_identifier="P903",
            name="Registration Patient",
            age=33,
            contact_number="000",
        )
        session.add(first_doctor)
        session.add(second_doctor)
        session.add(patient)
        session.flush()
        user = _patient_user(23, patient.id)
        session.add(user)
        first = RegistrationRequest(patient_id=user.id, doctor_id=first_doctor.id)
        second = RegistrationRequest(patient_id=user.id, doctor_id=second_doctor.id)
        session.add(first)
        session.add(second)
        session.commit()

        approve_registration_request(first.id, first_doctor, session)
        session.refresh(patient)
        session.refresh(second)
        assert patient.doctor_id == first_doctor.id
        assert second.status == "declined"

        with pytest.raises(HTTPException) as error:
            approve_registration_request(second.id, second_doctor, session)
        assert error.value.status_code == 409
        session.refresh(patient)
        assert patient.doctor_id == first_doctor.id


def test_account_closure_revokes_tokens_and_retains_patient_record():
    with _memory_session() as session:
        patient = Patient(
            patient_identifier="P904",
            name="Closing Patient",
            age=34,
            contact_number="000",
        )
        session.add(patient)
        session.flush()
        user = _patient_user(24, patient.id)
        session.add(user)
        session.commit()
        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
            token_version=user.token_version,
        )

        close_patient_account(CloseAccountRequest(confirmation="CLOSE"), user, session)
        session.refresh(user)
        assert user.is_active is False
        assert user.token_version == 1
        assert session.get(Patient, patient.id) is not None
        with pytest.raises(HTTPException) as error:
            get_current_user(authorization=f"Bearer {token}", session=session)
        assert error.value.status_code == 401


def test_custom_hours_replace_recurring_hours_and_blocks_are_separate():
    with _memory_session() as session:
        doctor = _doctor(15)
        session.add(doctor)
        local_date = _future_local_date(days=4)
        _add_availability(session, doctor.id, local_date)
        session.commit()

        create_schedule_exception(
            ScheduleExceptionIn(
                exception_date=local_date,
                kind="custom",
                start_time="14:00",
                end_time="16:00",
                slot_duration_minutes=30,
                timezone="Asia/Karachi",
            ),
            doctor,
            session,
        )
        create_schedule_exception(
            ScheduleExceptionIn(
                exception_date=local_date,
                kind="blocked_interval",
                start_time="15:00",
                end_time="15:30",
                timezone="Asia/Karachi",
            ),
            doctor,
            session,
        )
        assert _effective_windows_for_date(session, doctor.id, local_date) == [
            ("14:00", "15:00", 30),
            ("15:30", "16:00", 30),
        ]


def test_custom_hours_cannot_be_deleted_when_future_booking_depends_on_them():
    with _memory_session() as session:
        doctor = _doctor(16)
        patient = Patient(
            patient_identifier="P905",
            name="Custom Hours Patient",
            age=35,
            contact_number="000",
            doctor_id=doctor.id,
        )
        session.add(doctor)
        session.add(patient)
        session.flush()
        patient_user = _patient_user(25, patient.id)
        session.add(patient_user)
        local_date = _future_local_date(days=5)
        _add_availability(session, doctor.id, local_date)
        session.commit()

        custom = create_schedule_exception(
            ScheduleExceptionIn(
                exception_date=local_date,
                kind="custom",
                start_time="14:00",
                end_time="16:00",
                slot_duration_minutes=30,
                timezone="Asia/Karachi",
            ),
            doctor,
            session,
        )
        start_at, end_at = _local_slot_to_utc(
            local_date, "14:00", "14:30", "Asia/Karachi"
        )
        session.add(
            Appointment(
                doctor_id=doctor.id,
                patient_id=patient_user.id,
                appointment_date=local_date,
                start_time="14:00",
                end_time="14:30",
                timezone="Asia/Karachi",
                schedule_timezone="Asia/Karachi",
                start_at_utc=start_at.replace(tzinfo=None),
                end_at_utc=end_at.replace(tzinfo=None),
                status="booked",
            )
        )
        session.commit()

        with pytest.raises(HTTPException) as error:
            delete_schedule_exception(custom.exception.id, doctor, session)
        assert error.value.status_code == 409
        assert session.get(DoctorScheduleException, custom.exception.id) is not None


def test_nonexistent_dst_local_time_is_rejected():
    with pytest.raises(ValueError, match="daylight-saving time gap"):
        _local_slot_to_utc("2026-03-08", "02:30", "03:00", "America/New_York")

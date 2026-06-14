from datetime import datetime

import pytest
from fastapi import Response
from sqlmodel import Session, SQLModel, create_engine

from app.api.dashboard import get_dashboard_stats, get_weekly_assessments
from app.api.patient_portal import get_patient_assessments, get_patient_profile
from app.models import (
    AuthUser,
    GDMAssessment,
    MaternalHealthAssessment,
    Patient,
    UltrasoundImage,
    Visit,
)
from app.services.data_entry_service import DataEntryService


def _memory_session() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _user(role: str, user_id: int, patient_id: int | None = None) -> AuthUser:
    return AuthUser(
        id=user_id,
        email=f"{role}-{user_id}@example.com",
        password_hash="test",
        role=role,
        patient_id=patient_id,
    )


def test_patient_profile_exposes_safe_outcomes_without_confidence_or_provenance():
    with _memory_session() as session:
        patient = Patient(
            patient_identifier="P100",
            name="Portal Patient",
            age=30,
            contact_number="000",
        )
        session.add(patient)
        session.flush()
        patient_user = _user("patient", 100, patient.id)
        session.add(patient_user)
        visit = Visit(patient_id=patient.id, visit_date=datetime.utcnow())
        session.add(visit)
        session.flush()
        session.add(
            GDMAssessment(
                visit_id=visit.id,
                risk_level=2,
                confidence=0.91,
                ai_report="Completed GDM report",
                prediction_status="completed",
                severity="high",
                predicted_class="positive",
                oldest_input_age_days=45,
                has_stale_inputs=False,
                input_provenance={"ogtt": {"age_days": 45, "freshness": "aging"}},
            )
        )
        session.commit()

        profile = get_patient_profile("P100", patient_user, session)

        assert profile.latest_assessment_outcomes == {"gdm_risk_level": 2}
        assert profile.latest_assessment_freshness == {
            "gdm": {
                "oldest_input_age_days": 45,
                "has_stale_inputs": False,
            }
        }
        assert "input_provenance" not in profile.latest_assessment_freshness["gdm"]


def test_patient_assessment_response_hides_confidence_but_doctor_can_receive_it():
    with _memory_session() as session:
        doctor = _user("doctor", 10)
        patient = Patient(
            patient_identifier="P101",
            name="Portal Patient",
            age=30,
            contact_number="000",
            doctor_id=doctor.id,
        )
        session.add(doctor)
        session.add(patient)
        session.flush()
        patient_user = _user("patient", 11, patient.id)
        session.add(patient_user)
        visit = Visit(patient_id=patient.id, visit_date=datetime.utcnow())
        session.add(visit)
        session.flush()
        session.add(
            GDMAssessment(
                visit_id=visit.id,
                confidence=0.88,
                prediction_status="completed",
                severity="low",
                predicted_class="negative",
            )
        )
        session.commit()

        patient_payload = get_patient_assessments("P101", patient_user, session)
        doctor_payload = get_patient_assessments("P101", doctor, session)

        assert "confidence" not in patient_payload["gdm_assessments"][0]
        assert doctor_payload["gdm_assessments"][0]["confidence"] == 0.88


def test_ultrasound_delete_requires_patient_uploader_or_assigned_doctor():
    with _memory_session() as session:
        doctor = _user("doctor", 20)
        patient = Patient(
            patient_identifier="P102",
            name="Portal Patient",
            age=30,
            contact_number="000",
            doctor_id=doctor.id,
        )
        session.add(doctor)
        session.add(patient)
        session.flush()
        patient_user = _user("patient", 21, patient.id)
        session.add(patient_user)
        visit = Visit(patient_id=patient.id, visit_date=datetime.utcnow())
        session.add(visit)
        session.flush()
        patient_image = UltrasoundImage(
            visit_id=visit.id,
            patient_id=patient.id,
            public_id="patient-image",
            secure_url="https://example.com/patient.png",
            uploaded_by_role="patient",
            uploaded_by_user_id=patient_user.id,
        )
        doctor_image = UltrasoundImage(
            visit_id=visit.id,
            patient_id=patient.id,
            public_id="doctor-image",
            secure_url="https://example.com/doctor.png",
            uploaded_by_role="doctor",
            uploaded_by_user_id=doctor.id,
        )
        service = DataEntryService(session)

        service._validate_delete_access(patient, patient_image, patient_user)
        service._validate_delete_access(patient, doctor_image, doctor)
        with pytest.raises(ValueError, match="only delete ultrasound images they uploaded"):
            service._validate_delete_access(patient, doctor_image, patient_user)


def test_preeclampsia_is_included_in_weekly_assessment_counts_and_activity():
    with _memory_session() as session:
        doctor = _user("doctor", 30)
        patient = Patient(
            patient_identifier="P103",
            name="Portal Patient",
            age=30,
            contact_number="000",
            doctor_id=doctor.id,
        )
        session.add(doctor)
        session.add(patient)
        session.flush()
        visit = Visit(patient_id=patient.id, visit_date=datetime.utcnow())
        session.add(visit)
        session.flush()
        session.add(
            MaternalHealthAssessment(
                visit_id=visit.id,
                risk_level=1,
                confidence=0.75,
                ai_report="Preeclampsia report",
                prediction_status="completed",
                severity="medium",
                predicted_class="Mid Risk",
            )
        )
        session.commit()

        stats = get_dashboard_stats(Response(), doctor, session)
        activity = get_weekly_assessments(doctor, session)

        assert stats["assessments_this_week"] == 1
        assert len(activity) == 1
        assert activity[0]["assessment_type"] == "Maternal"
        assert activity[0]["preeclampsia"]["risk_level"] == 1

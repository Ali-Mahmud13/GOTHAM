"""Patient Portal API routes - for patient-facing platform."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_session
from app.models.patient import Patient, Visit
from app.models.assessments import (
    GDMAssessment,
    AnemiaAssessment,
    FetalHealthAssessment,
    MaternalHealthAssessment,
)
from app.models.auth import AuthUser
from app.core.security import get_current_user_compat, assert_patient_access
from app.api.patients import _latest_assessment_summary

router = APIRouter(prefix="/api/patient-portal", tags=["patient-portal"])


class PatientProfileResponse(BaseModel):
    """Schema for patient profile response."""

    id: int
    patient_identifier: str
    name: str
    age: int
    contact_number: str
    clinical_notes: str | None = None
    doctor_id: int | None = None
    is_registered_with_doctor: bool = False
    risk_level: str
    number_of_pregnancies: int | None
    gestation_in_previous_pregnancy: int | None
    bmi_category: int | None
    family_history: bool | None
    pcos: bool | None
    unexplained_prenatal_loss: bool | None
    large_child_or_birth_default: bool | None
    prediabetes: bool | None
    created_at: datetime
    updated_at: datetime
    latest_assessment_type: str | None = None
    latest_assessment_at: datetime | None = None
    latest_assessment_outcomes: dict[str, str | int | float | None] | None = None
    latest_assessment_freshness: dict[str, dict] | None = None

    class Config:
        from_attributes = True


class VisitResponse(BaseModel):
    """Schema for visit response."""

    id: int
    patient_id: int
    visit_date: datetime
    visit_type: str | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class PatientProfileUpdateRequest(BaseModel):
    """Schema for updating patient profile."""

    age: int | None = None
    contact_number: str | None = None
    number_of_pregnancies: int | None = None
    gestation_in_previous_pregnancy: int | None = None
    bmi_category: int | None = None
    family_history: bool | None = None
    pcos: bool | None = None
    unexplained_prenatal_loss: bool | None = None
    large_child_or_birth_default: bool | None = None
    prediabetes: bool | None = None


def _get_patient_or_404(session: Session, patient_identifier: str) -> Patient:
    patient = session.exec(select(Patient).where(Patient.patient_identifier == patient_identifier)).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/profile/{patient_identifier}", response_model=PatientProfileResponse)
def get_patient_profile(
    patient_identifier: str,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Get patient profile (patient: own record; doctor: assigned patients only)."""
    patient = _get_patient_or_404(session, patient_identifier)
    assert_patient_access(user, patient)

    clinical_notes = patient.clinical_notes if patient.doctor_id else None
    assessment = _latest_assessment_summary(session, patient.id)
    outcomes = assessment["outcomes"] or None
    patient_safe_outcomes = (
        {
            key: value
            for key, value in outcomes.items()
            if not key.endswith("_confidence")
        }
        if outcomes
        else None
    )
    freshness = assessment["freshness"] or None
    patient_safe_freshness = (
        {
            model: {
                "oldest_input_age_days": details.get("oldest_input_age_days"),
                "has_stale_inputs": bool(details.get("has_stale_inputs")),
            }
            for model, details in freshness.items()
        }
        if freshness
        else None
    )

    return PatientProfileResponse(
        id=patient.id,
        patient_identifier=patient.patient_identifier,
        name=patient.name,
        age=patient.age,
        contact_number=patient.contact_number,
        clinical_notes=clinical_notes,
        doctor_id=patient.doctor_id,
        is_registered_with_doctor=bool(patient.doctor_id),
        risk_level=patient.risk_level,
        number_of_pregnancies=patient.number_of_pregnancies,
        gestation_in_previous_pregnancy=patient.gestation_in_previous_pregnancy,
        bmi_category=patient.bmi_category,
        family_history=patient.family_history,
        pcos=patient.pcos,
        unexplained_prenatal_loss=patient.unexplained_prenatal_loss,
        large_child_or_birth_default=patient.large_child_or_birth_default,
        prediabetes=patient.prediabetes,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
        latest_assessment_type=assessment["type"],
        latest_assessment_at=assessment["created_at"],
        latest_assessment_outcomes=patient_safe_outcomes,
        latest_assessment_freshness=patient_safe_freshness,
    )


@router.put("/profile/{patient_identifier}", response_model=PatientProfileResponse)
def update_patient_profile(
    patient_identifier: str,
    update_data: PatientProfileUpdateRequest,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Update patient profile (patient: own; doctor: assigned patients)."""
    patient = _get_patient_or_404(session, patient_identifier)
    assert_patient_access(user, patient)

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(patient, key, value)

    patient.updated_at = datetime.utcnow()
    session.add(patient)
    session.commit()
    session.refresh(patient)

    return get_patient_profile(patient_identifier, user, session)


@router.get("/visits/{patient_identifier}", response_model=List[VisitResponse])
def get_patient_visits(
    patient_identifier: str,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Get all visits for a specific patient."""
    patient = _get_patient_or_404(session, patient_identifier)
    assert_patient_access(user, patient)

    visits_statement = (
        select(Visit).where(Visit.patient_id == patient.id).order_by(Visit.visit_date.desc())
    )
    visits = session.exec(visits_statement).all()
    return visits


@router.get("/assessments/{patient_identifier}")
def get_patient_assessments(
    patient_identifier: str,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Get structured assessments for a patient without exposing raw model inputs."""
    patient = _get_patient_or_404(session, patient_identifier)
    assert_patient_access(user, patient)

    def get_rows(model):
        return session.exec(
            select(model)
            .join(Visit, model.visit_id == Visit.id)
            .where(Visit.patient_id == patient.id)
            .order_by(model.created_at.desc())
        ).all()

    def serialize(model_name: str, assessment) -> dict:
        payload = {
            "id": assessment.id,
            "visit_id": assessment.visit_id,
            "model": model_name,
            "created_at": assessment.created_at,
            "prediction_status": assessment.prediction_status,
            "severity": assessment.severity,
            "predicted_class": assessment.predicted_class,
            "oldest_input_age_days": assessment.oldest_input_age_days,
            "has_stale_inputs": bool(assessment.has_stale_inputs),
        }
        if user.role == "doctor":
            payload["confidence"] = assessment.confidence
        return payload

    return {
        "gdm_assessments": [
            serialize("gdm", assessment) for assessment in get_rows(GDMAssessment)
        ],
        "anemia_assessments": [
            serialize("anemia", assessment) for assessment in get_rows(AnemiaAssessment)
        ],
        "fetal_assessments": [
            serialize("fetal", assessment) for assessment in get_rows(FetalHealthAssessment)
        ],
        "preeclampsia_assessments": [
            serialize("preeclampsia", assessment)
            for assessment in get_rows(MaternalHealthAssessment)
        ],
    }

"""Patient Portal API routes - for patient-facing platform."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_session
from app.models.patient import Patient, Visit
from app.models.assessments import GDMAssessment, AnemiaAssessment, FetalHealthAssessment
from app.models.auth import AuthUser
from app.core.security import get_current_user_compat, assert_patient_access

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
    bmi_category: int | None
    family_history: bool | None
    pcos: bool | None
    unexplained_prenatal_loss: bool | None
    large_child_or_birth_default: bool | None
    prediabetes: bool | None
    created_at: datetime
    updated_at: datetime

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
        bmi_category=patient.bmi_category,
        family_history=patient.family_history,
        pcos=patient.pcos,
        unexplained_prenatal_loss=patient.unexplained_prenatal_loss,
        large_child_or_birth_default=patient.large_child_or_birth_default,
        prediabetes=patient.prediabetes,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
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
    """Get all assessments for a specific patient."""
    patient = _get_patient_or_404(session, patient_identifier)
    assert_patient_access(user, patient)

    gdm_statement = (
        select(GDMAssessment)
        .where(GDMAssessment.patient_identifier == patient_identifier)
        .order_by(GDMAssessment.timestamp.desc())
    )
    gdm_assessments = session.exec(gdm_statement).all()

    anemia_statement = (
        select(AnemiaAssessment)
        .where(AnemiaAssessment.patient_identifier == patient_identifier)
        .order_by(AnemiaAssessment.timestamp.desc())
    )
    anemia_assessments = session.exec(anemia_statement).all()

    fetal_statement = (
        select(FetalHealthAssessment)
        .where(FetalHealthAssessment.patient_identifier == patient_identifier)
        .order_by(FetalHealthAssessment.timestamp.desc())
    )
    fetal_assessments = session.exec(fetal_statement).all()

    return {
        "gdm_assessments": [
            {
                "id": a.id,
                "timestamp": a.timestamp,
                "risk_prediction": a.risk_prediction,
                "input_features": a.input_features,
            }
            for a in gdm_assessments
        ],
        "anemia_assessments": [
            {
                "id": a.id,
                "timestamp": a.timestamp,
                "risk_prediction": a.risk_prediction,
                "input_features": a.input_features,
            }
            for a in anemia_assessments
        ],
        "fetal_assessments": [
            {
                "id": a.id,
                "timestamp": a.timestamp,
                "risk_prediction": a.risk_prediction,
                "input_features": a.input_features,
            }
            for a in fetal_assessments
        ],
    }

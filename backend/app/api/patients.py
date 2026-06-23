"""Patient API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import func

from app.db.session import get_session
from app.models.patient import Patient, Visit
from app.models.assessments import (
    GDMAssessment,
    AnemiaAssessment,
    FetalHealthAssessment,
    MaternalHealthAssessment,
)
from app.models.auth import AuthUser
from app.core.security import get_current_user_compat, assert_patient_access, require_role

router = APIRouter(prefix="/api/patients", tags=["patients"])


class PatientCreate(BaseModel):
    """Schema for creating a patient."""

    patient_identifier: str | None = None
    name: str
    age: int
    contact_number: str
    clinical_notes: str | None = None
    doctor_id: int | None = None
    number_of_pregnancies: int | None = None
    gestation_in_previous_pregnancy: int | None = None
    bmi_category: int | None = None
    family_history: bool | None = None
    pcos: bool | None = None
    unexplained_prenatal_loss: bool | None = None
    large_child_or_birth_default: bool | None = None
    prediabetes: bool | None = None


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""

    name: str | None = None
    age: int | None = None
    contact_number: str | None = None
    clinical_notes: str | None = None
    number_of_pregnancies: int | None = None
    gestation_in_previous_pregnancy: int | None = None
    bmi_category: int | None = None
    family_history: bool | None = None
    pcos: bool | None = None
    unexplained_prenatal_loss: bool | None = None
    large_child_or_birth_default: bool | None = None
    prediabetes: bool | None = None


class PatientResponse(BaseModel):
    """Schema for patient response."""

    id: int
    patient_identifier: str
    name: str
    age: int
    contact_number: str
    clinical_notes: str | None
    risk_level: str
    doctor_id: int | None
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
    latest_ai_report: str | None = None
    latest_assessment_type: str | None = None
    latest_assessment_at: datetime | None = None
    latest_assessment_outcomes: dict[str, str | int | float | None] | None = None
    latest_assessment_freshness: dict | None = None

    class Config:
        from_attributes = True


def _latest_assessment_summary(session: Session, patient_id: int) -> dict:
    """Return the newest completed assessment across all visits and model tables."""
    candidates: list[tuple[str, object]] = []
    assessment_models = [
        ("gdm", GDMAssessment),
        ("anemia", AnemiaAssessment),
        ("fetal", FetalHealthAssessment),
        ("preeclampsia", MaternalHealthAssessment),
    ]

    for kind, model in assessment_models:
        rows = session.exec(
            select(model)
            .join(Visit, model.visit_id == Visit.id)
            .where(Visit.patient_id == patient_id)
            .where(model.ai_report.is_not(None))
            .where(model.prediction_status == "completed")
        ).all()
        candidates.extend(
            (kind, row)
            for row in rows
            if isinstance(row.ai_report, str) and row.ai_report.strip()
        )

    if not candidates:
        return {
            "report": None,
            "type": None,
            "created_at": None,
            "outcomes": None,
            "freshness": None,
        }

    latest_kind, latest_row = max(candidates, key=lambda item: item[1].created_at)
    related = [
        (kind, row)
        for kind, row in candidates
        if row.visit_id == latest_row.visit_id and row.ai_report == latest_row.ai_report
    ]
    related_kinds = {kind for kind, _ in related}

    if "fetal" in related_kinds and related_kinds.intersection({"gdm", "anemia", "preeclampsia"}):
        assessment_type = "both"
    elif latest_kind == "fetal":
        assessment_type = "fetal"
    else:
        assessment_type = "maternal"

    outcomes: dict[str, str | int | float | None] = {}
    freshness: dict[str, dict] = {}
    for kind, row in related:
        if kind == "gdm":
            outcomes["gdm_risk_level"] = row.risk_level
            outcomes["gdm_confidence"] = row.confidence
        elif kind == "anemia":
            outcomes["anemia_diagnosis"] = row.diagnosis
            outcomes["anemia_confidence"] = row.confidence
        elif kind == "fetal":
            outcomes["fetal_health_status"] = row.status
            outcomes["fetal_confidence"] = row.confidence
        elif kind == "preeclampsia":
            outcomes["preeclampsia_risk_level"] = row.risk_level
            outcomes["preeclampsia_confidence"] = row.confidence
        freshness[kind] = {
            "oldest_input_age_days": row.oldest_input_age_days,
            "has_stale_inputs": row.has_stale_inputs,
            "input_provenance": row.input_provenance or {},
        }

    return {
        "report": latest_row.ai_report,
        "type": assessment_type,
        "created_at": latest_row.created_at,
        "outcomes": outcomes,
        "freshness": freshness,
    }


@router.get("/", response_model=List[PatientResponse])
def get_all_patients(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """List patients for the authenticated doctor (assigned) or patient (self)."""
    if user.role == "doctor":
        statement = select(Patient).where(Patient.doctor_id == user.id).order_by(Patient.id)
        patients = session.exec(statement).all()
        return patients
    elif user.role == "patient":
        if not user.patient_id:
            return []
        patient = session.get(Patient, user.patient_id)
        return [patient] if patient else []
    
    raise HTTPException(status_code=403, detail="Insufficient permissions")



@router.get("/{patient_identifier}", response_model=PatientResponse)
def get_patient(
    patient_identifier: str,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Get a specific patient by identifier (authorized patient or assigned doctor)."""
    statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(statement).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    assert_patient_access(user, patient)

    assessment = _latest_assessment_summary(session, patient.id)

    payload = patient.model_dump()
    payload["latest_ai_report"] = assessment["report"]
    payload["latest_assessment_type"] = assessment["type"]
    payload["latest_assessment_at"] = assessment["created_at"]
    payload["latest_assessment_outcomes"] = assessment["outcomes"]
    payload["latest_assessment_freshness"] = assessment["freshness"]

    return payload


def get_next_patient_id(session: Session) -> str:
    """Generate the next available patient ID in format P001, P002, etc."""
    from sqlalchemy import cast, Integer
    
    max_id = session.exec(
        select(func.max(cast(func.substr(Patient.patient_identifier, 2), Integer)))
        .where(Patient.patient_identifier.like("P%"))
    ).one()
    
    max_num = max_id or 0
    return f"P{max_num + 1:03d}"


@router.post("/", response_model=PatientResponse)
def create_patient(
    patient_data: PatientCreate,
    user: AuthUser = Depends(require_role("doctor")),
    session: Session = Depends(get_session),
):
    """Create a new patient (doctor only)."""
    if not patient_data.patient_identifier:
        patient_data.patient_identifier = get_next_patient_id(session)

    statement = select(Patient).where(Patient.patient_identifier == patient_data.patient_identifier)
    existing = session.exec(statement).first()

    if existing:
        raise HTTPException(status_code=400, detail="Patient identifier already exists")

    patient_dict = patient_data.model_dump()
    if not patient_dict.get("doctor_id"):
        patient_dict["doctor_id"] = user.id

    patient = Patient(**patient_dict)
    session.add(patient)
    session.commit()
    session.refresh(patient)

    return patient


@router.put("/{patient_identifier}", response_model=PatientResponse)
def update_patient(
    patient_identifier: str,
    patient_data: PatientUpdate,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Update a patient (doctor: assigned patient; patient: own demographics per portal rules)."""
    statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(statement).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    assert_patient_access(user, patient)

    for key, value in patient_data.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)

    patient.updated_at = datetime.utcnow()
    session.add(patient)
    session.commit()
    session.refresh(patient)

    return patient


@router.delete("/{patient_identifier}")
def delete_patient(
    patient_identifier: str,
    user: AuthUser = Depends(require_role("doctor")),
    session: Session = Depends(get_session),
):
    """Hard deletion is disabled; doctors must unregister patients instead."""
    statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(statement).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if patient.doctor_id != user.id:
        raise HTTPException(status_code=403, detail="You may only delete patients registered with you")

    raise HTTPException(
        status_code=405,
        detail="Patient records cannot be permanently deleted by doctors. Unregister the patient instead.",
    )

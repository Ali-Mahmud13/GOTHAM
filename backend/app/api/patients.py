"""Patient API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_session
from app.models.patient import Patient, Visit
from app.models.assessments import GDMAssessment, AnemiaAssessment, FetalHealthAssessment
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
    risk_level: str = "low"
    doctor_id: int | None = None
    number_of_pregnancies: int | None = None
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
    risk_level: str | None = None
    number_of_pregnancies: int | None = None
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

    class Config:
        from_attributes = True


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

    latest_visit = session.exec(
        select(Visit).where(Visit.patient_id == patient.id).order_by(Visit.visit_date.desc())
    ).first()
    latest_ai_report = None
    latest_assessment_type = None

    if latest_visit:
        gdm = session.exec(
            select(GDMAssessment).where(GDMAssessment.visit_id == latest_visit.id)
        ).first()
        anemia = session.exec(
            select(AnemiaAssessment).where(AnemiaAssessment.visit_id == latest_visit.id)
        ).first()
        fetal = session.exec(
            select(FetalHealthAssessment).where(FetalHealthAssessment.visit_id == latest_visit.id)
        ).first()

        for assessment_type, report in [
            ("both", (fetal.ai_report if fetal and fetal.ai_report else None)),
            ("maternal", (anemia.ai_report if anemia and anemia.ai_report else None)),
            ("maternal", (gdm.ai_report if gdm and gdm.ai_report else None)),
            ("fetal", (fetal.ai_report if fetal and fetal.ai_report else None)),
        ]:
            if report:
                latest_ai_report = report
                latest_assessment_type = assessment_type
                break
    payload = patient.model_dump()
    payload["latest_ai_report"] = latest_ai_report
    payload["latest_assessment_type"] = latest_assessment_type

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
    """Delete a patient (doctor only, assigned patients)."""
    statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(statement).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if patient.doctor_id != user.id:
        raise HTTPException(status_code=403, detail="You may only delete patients registered with you")

    session.delete(patient)
    session.commit()

    return {"message": "Patient deleted successfully"}

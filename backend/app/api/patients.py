"""Patient API routes."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_session
from app.models.patient import Patient, Visit
from app.models.assessments import GDMAssessment, AnemiaAssessment, FetalHealthAssessment
from app.models.auth import AuthUser

router = APIRouter(prefix="/api/patients", tags=["patients"])


# Pydantic models for API requests/responses
class PatientCreate(BaseModel):
    """Schema for creating a patient."""
    patient_identifier: Optional[str] = None
    name: str
    age: int
    contact_number: str
    clinical_notes: Optional[str] = None
    risk_level: str = "low"
    doctor_id: Optional[int] = None
    number_of_pregnancies: Optional[int] = None
    bmi_category: Optional[int] = None
    family_history: Optional[bool] = None
    pcos: Optional[bool] = None
    unexplained_prenatal_loss: Optional[bool] = None
    large_child_or_birth_default: Optional[bool] = None
    prediabetes: Optional[bool] = None


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""
    name: Optional[str] = None
    age: Optional[int] = None
    contact_number: Optional[str] = None
    clinical_notes: Optional[str] = None
    risk_level: Optional[str] = None
    number_of_pregnancies: Optional[int] = None
    bmi_category: Optional[int] = None
    family_history: Optional[bool] = None
    pcos: Optional[bool] = None
    unexplained_prenatal_loss: Optional[bool] = None
    large_child_or_birth_default: Optional[bool] = None
    prediabetes: Optional[bool] = None


class PatientResponse(BaseModel):
    """Schema for patient response."""
    id: int
    patient_identifier: str
    name: str
    age: int
    contact_number: str
    clinical_notes: Optional[str]
    risk_level: str
    doctor_id: Optional[int]
    number_of_pregnancies: Optional[int]
    bmi_category: Optional[int]
    family_history: Optional[bool]
    pcos: Optional[bool]
    unexplained_prenatal_loss: Optional[bool]
    large_child_or_birth_default: Optional[bool]
    prediabetes: Optional[bool]
    created_at: datetime
    updated_at: datetime
    latest_ai_report: Optional[str] = None
    latest_assessment_type: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[PatientResponse])
def get_all_patients(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session)
):
    """Get all patients (filtered by doctor if authenticated)."""
    # Get authenticated user
    user = None
    if user_email:
        user = session.exec(
            select(AuthUser).where(AuthUser.email == user_email)
        ).first()
    
    # For doctors, filter by their assigned patients
    if user and user.role == "doctor":
        statement = select(Patient).where(Patient.doctor_id == user.id).order_by(Patient.id)
    else:
        # For patients or unauthenticated, return all (can be restricted later)
        statement = select(Patient).order_by(Patient.id)
    
    patients = session.exec(statement).all()
    return patients


@router.get("/{patient_identifier}", response_model=PatientResponse)
def get_patient(patient_identifier: str, session: Session = Depends(get_session)):
    """Get a specific patient by identifier."""
    statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(statement).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    latest_visit = session.exec(select(Visit).where(Visit.patient_id == patient.id).order_by(Visit.visit_date.desc())).first()
    latest_ai_report = None
    latest_assessment_type = None

    if latest_visit:
        gdm = session.exec(select(GDMAssessment).where(GDMAssessment.visit_id == latest_visit.id)).first()
        anemia = session.exec(select(AnemiaAssessment).where(AnemiaAssessment.visit_id == latest_visit.id)).first()
        fetal = session.exec(select(FetalHealthAssessment).where(FetalHealthAssessment.visit_id == latest_visit.id)).first()

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
    statement = select(Patient).order_by(Patient.patient_identifier.desc())
    patients = session.exec(statement).all()
    
    if not patients:
        return "P001"
    
    # Extract numeric parts from patient IDs and find the maximum
    max_num = 0
    for patient in patients:
        # Extract number from format like P001, P002, etc.
        if patient.patient_identifier.startswith('P') and len(patient.patient_identifier) > 1:
            try:
                num = int(patient.patient_identifier[1:])
                max_num = max(max_num, num)
            except ValueError:
                continue
    
    # Generate next ID
    next_num = max_num + 1
    return f"P{next_num:03d}"


@router.post("/", response_model=PatientResponse)
def create_patient(
    patient_data: PatientCreate,
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session)
):
    """Create a new patient."""
    # Get authenticated user
    user = None
    if user_email:
        user = session.exec(
            select(AuthUser).where(AuthUser.email == user_email)
        ).first()
    
    # Auto-generate patient_identifier if not provided
    if not patient_data.patient_identifier:
        patient_data.patient_identifier = get_next_patient_id(session)
    
    # Check if patient already exists
    statement = select(Patient).where(Patient.patient_identifier == patient_data.patient_identifier)
    existing = session.exec(statement).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Patient identifier already exists")
    
    patient_dict = patient_data.dict()
    
    # Assign to logged-in doctor if no doctor_id provided and user is a doctor
    if not patient_dict.get('doctor_id') and user and user.role == "doctor":
        patient_dict['doctor_id'] = user.id
    
    patient = Patient(**patient_dict)
    session.add(patient)
    session.commit()
    session.refresh(patient)
    
    return patient


@router.put("/{patient_identifier}", response_model=PatientResponse)
def update_patient(
    patient_identifier: str,
    patient_data: PatientUpdate,
    session: Session = Depends(get_session)
):
    """Update a patient."""
    statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(statement).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Update fields
    for key, value in patient_data.dict(exclude_unset=True).items():
        setattr(patient, key, value)
    
    patient.updated_at = datetime.utcnow()
    session.add(patient)
    session.commit()
    session.refresh(patient)
    
    return patient


@router.delete("/{patient_identifier}")
def delete_patient(patient_identifier: str, session: Session = Depends(get_session)):
    """Delete a patient."""
    statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(statement).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    session.delete(patient)
    session.commit()
    
    return {"message": "Patient deleted successfully"}
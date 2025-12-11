"""Patient API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_session
from app.models.patient import Patient, Visit
from app.models.assessments import GDMAssessment, AnemiaAssessment, FetalHealthAssessment

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
    number_of_pregnancies: Optional[int]
    bmi_category: Optional[int]
    family_history: Optional[bool]
    pcos: Optional[bool]
    unexplained_prenatal_loss: Optional[bool]
    large_child_or_birth_default: Optional[bool]
    prediabetes: Optional[bool]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[PatientResponse])
def get_all_patients(session: Session = Depends(get_session)):
    """Get all patients."""
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
    
    return patient


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
def create_patient(patient_data: PatientCreate, session: Session = Depends(get_session)):
    """Create a new patient."""
    # Auto-generate patient_identifier if not provided
    if not patient_data.patient_identifier:
        patient_data.patient_identifier = get_next_patient_id(session)
    
    # Check if patient already exists
    statement = select(Patient).where(Patient.patient_identifier == patient_data.patient_identifier)
    existing = session.exec(statement).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Patient identifier already exists")
    
    patient = Patient(**patient_data.dict())
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
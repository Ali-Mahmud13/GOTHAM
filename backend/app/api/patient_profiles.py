"""Patient Profile API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_session
from app.models.patient import PatientProfile, Patient

router = APIRouter(prefix="/api/patient-profiles", tags=["patient-profiles"])


# Pydantic schemas
class PatientProfileCreate(BaseModel):
    """Schema for creating a patient profile."""
    patient_identifier: str
    name: str
    age: int
    contact_number: str
    doctor_notes: Optional[str] = None
    ai_report: Optional[str] = None
    risk_level: str = "low"


class PatientProfileUpdate(BaseModel):
    """Schema for updating a patient profile."""
    name: Optional[str] = None
    age: Optional[int] = None
    contact_number: Optional[str] = None
    doctor_notes: Optional[str] = None
    ai_report: Optional[str] = None
    risk_level: Optional[str] = None


class PatientProfileResponse(BaseModel):
    """Schema for patient profile response."""
    id: int
    patient_identifier: str
    name: str
    age: int
    contact_number: str
    doctor_notes: Optional[str]
    ai_report: Optional[str]
    risk_level: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router. get("/", response_model=List[PatientProfileResponse])
def get_all_profiles(session: Session = Depends(get_session)):
    """Get all patient profiles."""
    statement = select(PatientProfile).order_by(PatientProfile.patient_identifier)
    profiles = session.exec(statement).all()
    return profiles


@router.get("/{patient_identifier}", response_model=PatientProfileResponse)
def get_profile(patient_identifier: str, session: Session = Depends(get_session)):
    """Get a specific patient profile by identifier."""
    statement = select(PatientProfile).where(PatientProfile.patient_identifier == patient_identifier)
    profile = session. exec(statement).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    return profile


@router.post("/", response_model=PatientProfileResponse)
def create_profile(profile_data: PatientProfileCreate, session: Session = Depends(get_session)):
    """Create a new patient profile."""
    # Check if patient exists in patients table
    patient_statement = select(Patient).where(Patient.patient_identifier == profile_data.patient_identifier)
    patient = session.exec(patient_statement).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.  Create patient record first.")
    
    # Check if profile already exists
    existing_statement = select(PatientProfile).where(PatientProfile.patient_identifier == profile_data.patient_identifier)
    existing = session.exec(existing_statement). first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Patient profile already exists")
    
    profile = PatientProfile(**profile_data.dict())
    session.add(profile)
    session.commit()
    session.refresh(profile)
    
    return profile


@router.put("/{patient_identifier}", response_model=PatientProfileResponse)
def update_profile(
    patient_identifier: str,
    profile_data: PatientProfileUpdate,
    session: Session = Depends(get_session)
):
    """Update a patient profile."""
    statement = select(PatientProfile).where(PatientProfile.patient_identifier == patient_identifier)
    profile = session.exec(statement).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Update fields
    for key, value in profile_data.dict(exclude_unset=True). items():
        setattr(profile, key, value)
    
    profile.updated_at = datetime.utcnow()
    session. add(profile)
    session.commit()
    session.refresh(profile)
    
    return profile


@router.delete("/{patient_identifier}")
def delete_profile(patient_identifier: str, session: Session = Depends(get_session)):
    """Delete a patient profile."""
    statement = select(PatientProfile).where(PatientProfile.patient_identifier == patient_identifier)
    profile = session.exec(statement).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    session.delete(profile)
    session.commit()
    
    return {"message": "Patient profile deleted successfully"}
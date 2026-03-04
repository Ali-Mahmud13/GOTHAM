"""Patient Portal API routes - for patient-facing platform."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_session
from app.models.patient import Patient, Visit
from app.models.assessments import GDMAssessment, AnemiaAssessment, FetalHealthAssessment

router = APIRouter(prefix="/api/patient-portal", tags=["patient-portal"])


# Pydantic models for API requests/responses
class PatientLoginRequest(BaseModel):
    """Schema for patient login."""
    name: str


class PatientLoginResponse(BaseModel):
    """Schema for patient login response."""
    success: bool
    patient_identifier: Optional[str] = None
    name: Optional[str] = None
    message: str


class PatientProfileResponse(BaseModel):
    """Schema for patient profile response."""
    id: int
    patient_identifier: str
    name: str
    age: int
    contact_number: str
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


class VisitResponse(BaseModel):
    """Schema for visit response."""
    id: int
    patient_id: int
    visit_date: datetime
    visit_type: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PatientProfileUpdateRequest(BaseModel):
    """Schema for updating patient profile."""
    age: Optional[int] = None
    contact_number: Optional[str] = None
    number_of_pregnancies: Optional[int] = None
    bmi_category: Optional[int] = None
    family_history: Optional[bool] = None
    pcos: Optional[bool] = None
    unexplained_prenatal_loss: Optional[bool] = None
    large_child_or_birth_default: Optional[bool] = None
    prediabetes: Optional[bool] = None


@router.post("/login", response_model=PatientLoginResponse)
def patient_login(
    login_data: PatientLoginRequest,
    session: Session = Depends(get_session)
):
    """
    Patient login by name only (no password required).
    Returns patient identifier if found.
    """
    # Search for patient by name (case-insensitive)
    statement = select(Patient).where(Patient.name.ilike(f"%{login_data.name}%"))
    patients = session.exec(statement).all()
    
    if not patients:
        return PatientLoginResponse(
            success=False,
            message="Patient not found. Please check your name or contact your healthcare provider."
        )
    
    if len(patients) > 1:
        # Multiple matches - return list of names for user to be more specific
        names = [p.name for p in patients]
        return PatientLoginResponse(
            success=False,
            message=f"Multiple patients found: {', '.join(names)}. Please enter your full name."
        )
    
    # Single match found
    patient = patients[0]
    return PatientLoginResponse(
        success=True,
        patient_identifier=patient.patient_identifier,
        name=patient.name,
        message="Login successful"
    )


@router.get("/profile/{patient_identifier}", response_model=PatientProfileResponse)
def get_patient_profile(
    patient_identifier: str,
    session: Session = Depends(get_session)
):
    """
    Get patient profile by patient identifier.
    Patients can only access their own data.
    """
    statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(statement).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient


@router.put("/profile/{patient_identifier}", response_model=PatientProfileResponse)
def update_patient_profile(
    patient_identifier: str,
    update_data: PatientProfileUpdateRequest,
    session: Session = Depends(get_session)
):
    """
    Update patient profile information.
    Patients can update their own basic information.
    """
    statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(statement).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Update only provided fields
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(patient, key, value)
    
    patient.updated_at = datetime.utcnow()
    session.add(patient)
    session.commit()
    session.refresh(patient)
    
    return patient


@router.get("/visits/{patient_identifier}", response_model=List[VisitResponse])
def get_patient_visits(
    patient_identifier: str,
    session: Session = Depends(get_session)
):
    """
    Get all visits for a specific patient.
    """
    # Verify patient exists and get their ID
    patient_statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(patient_statement).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get all visits for this patient using patient_id (NOT patient_identifier)
    visits_statement = select(Visit).where(
        Visit.patient_id == patient.id
    ).order_by(Visit.visit_date.desc())
    visits = session.exec(visits_statement).all()
    
    return visits


@router.get("/assessments/{patient_identifier}")
def get_patient_assessments(
    patient_identifier: str,
    session: Session = Depends(get_session)
):
    """
    Get all assessments for a specific patient (GDM, Anemia, Fetal Health).
    """
    # Verify patient exists
    patient_statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
    patient = session.exec(patient_statement).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get latest assessments
    gdm_statement = select(GDMAssessment).where(
        GDMAssessment.patient_identifier == patient_identifier
    ).order_by(GDMAssessment.timestamp.desc())
    gdm_assessments = session.exec(gdm_statement).all()
    
    anemia_statement = select(AnemiaAssessment).where(
        AnemiaAssessment.patient_identifier == patient_identifier
    ).order_by(AnemiaAssessment.timestamp.desc())
    anemia_assessments = session.exec(anemia_statement).all()
    
    fetal_statement = select(FetalHealthAssessment).where(
        FetalHealthAssessment.patient_identifier == patient_identifier
    ).order_by(FetalHealthAssessment.timestamp.desc())
    fetal_assessments = session.exec(fetal_statement).all()
    
    return {
        "gdm_assessments": [
            {
                "id": a.id,
                "timestamp": a.timestamp,
                "risk_prediction": a.risk_prediction,
                "confidence": a.confidence,
                "input_features": a.input_features
            }
            for a in gdm_assessments
        ],
        "anemia_assessments": [
            {
                "id": a.id,
                "timestamp": a.timestamp,
                "risk_prediction": a.risk_prediction,
                "confidence": a.confidence,
                "input_features": a.input_features
            }
            for a in anemia_assessments
        ],
        "fetal_assessments": [
            {
                "id": a.id,
                "timestamp": a.timestamp,
                "risk_prediction": a.risk_prediction,
                "confidence": a.confidence,
                "input_features": a.input_features
            }
            for a in fetal_assessments
        ]
    }

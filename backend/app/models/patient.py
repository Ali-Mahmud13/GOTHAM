"""Patient and Visit models for gestational diabetes risk assessment."""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class Patient(SQLModel, table=True):
    """Patient model with static/semi-static features."""
    
    __tablename__ = "patients"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_identifier: str = Field(unique=True, index=True)
    
    # Static boolean features
    family_history: Optional[bool] = Field(default=None, description="Family history of diabetes")
    pcos: Optional[bool] = Field(default=None, description="Polycystic ovary syndrome")
    unexplained_prenatal_loss: Optional[bool] = Field(default=None, description="History of unexplained prenatal loss")
    large_child_or_birth_default: Optional[bool] = Field(default=None, description="History of large child or birth complications")
    prediabetes: Optional[bool] = Field(default=None, description="Pre-existing prediabetes condition")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime. utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to visits
    visits: List["Visit"] = Relationship(back_populates="patient")
    
    # NEW: Relationship to profile
    profile: Optional["PatientProfile"] = Relationship(back_populates="patient")


class PatientProfile(SQLModel, table=True):
    """Patient profile with personal information and clinical notes."""
    
    __tablename__ = "patient_profiles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_identifier: str = Field(unique=True, foreign_key="patients.patient_identifier", index=True)
    
    # Personal Information
    name: str = Field(description="Patient full name")
    age: int = Field(description="Patient age")
    contact_number: str = Field(description="Patient contact number")
    
    # Clinical Information
    doctor_notes: Optional[str] = Field(default=None, description="Doctor's clinical notes")
    ai_report: Optional[str] = Field(default=None, description="AI-generated risk assessment report")
    
    # Risk Level (calculated or manually set)
    risk_level: str = Field(default="low", description="Risk level: low, medium, high")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship back to patient
    patient: Optional[Patient] = Relationship(back_populates="profile")


class Visit(SQLModel, table=True):
    """Visit model with dynamic measurements collected during clinical visits."""
    
    __tablename__ = "visits"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patients.id", index=True)
    
    # Visit metadata
    visit_date: datetime = Field(description="Date of the clinical visit")
    visit_type: Optional[str] = Field(default=None, description="Type of visit (e.g., first_trimester, routine)")
    notes: Optional[str] = Field(default=None, description="Clinical notes")
    
    # Dynamic measurements
    age: Optional[int] = Field(default=None, description="Patient age at visit")
    bmi: Optional[float] = Field(default=None, description="Body Mass Index")
    sys_bp: Optional[int] = Field(default=None, description="Systolic blood pressure")
    dia_bp: Optional[int] = Field(default=None, description="Diastolic blood pressure")
    hdl: Optional[float] = Field(default=None, description="HDL cholesterol level")
    hemoglobin: Optional[float] = Field(default=None, description="Hemoglobin level")
    ogtt: Optional[float] = Field(default=None, description="Oral glucose tolerance test result")
    
    # Pregnancy-related features
    no_of_pregnancy: Optional[int] = Field(default=None, description="Number of pregnancies (cumulative)")
    gestation_in_previous_pregnancy: Optional[int] = Field(default=None, description="Gestation weeks in previous pregnancy")
    
    # Lifestyle assessment
    sedentary_lifestyle: Optional[bool] = Field(default=None, description="Sedentary lifestyle assessment")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime. utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to patient
    patient: Patient = Relationship(back_populates="visits")
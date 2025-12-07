"""Patient and Visit models for GOTHAM medical risk assessment system."""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class Patient(SQLModel, table=True):
    """Patient model with demographics and static medical history."""
    
    __tablename__ = "patients"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_identifier: str = Field(unique=True, index=True)
    
    # Personal Information (merged from PatientProfile)
    name: str = Field(description="Patient full name")
    age: int = Field(description="Patient age")
    contact_number: str = Field(description="Patient contact number")
    
    # Clinical Information
    clinical_notes: Optional[str] = Field(default=None, description="Clinical notes and history")
    risk_level: str = Field(default="low", description="Overall risk level: low, medium, high")
    
    # Static Medical History
    number_of_pregnancies: Optional[int] = Field(default=None, description="Total number of pregnancies")
    bmi_category: Optional[int] = Field(default=None, description="BMI category")
    family_history: Optional[bool] = Field(default=None, description="Family history of diabetes")
    pcos: Optional[bool] = Field(default=None, description="Polycystic ovary syndrome")
    unexplained_prenatal_loss: Optional[bool] = Field(default=None, description="History of unexplained prenatal loss")
    large_child_or_birth_default: Optional[bool] = Field(default=None, description="History of large child or birth complications")
    prediabetes: Optional[bool] = Field(default=None, description="Pre-existing prediabetes condition")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to visits
    visits: List["Visit"] = Relationship(back_populates="patient")


class Visit(SQLModel, table=True):
    """Visit model representing a single clinical appointment."""
    
    __tablename__ = "visits"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patients.id", index=True)
    
    # Visit metadata
    visit_date: datetime = Field(description="Date and time of the clinical visit", index=True)
    visit_type: Optional[str] = Field(default=None, description="Type of visit (e.g., first_trimester, routine)")
    notes: Optional[str] = Field(default=None, description="Doctor's clinical notes for this visit")  # Changed from doctor_notes
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    patient: Patient = Relationship(back_populates="visits")
    gdm_assessment: Optional["GDMAssessment"] = Relationship(back_populates="visit")
    anemia_assessment: Optional["AnemiaAssessment"] = Relationship(back_populates="visit")
    fetal_health_assessment: Optional["FetalHealthAssessment"] = Relationship(back_populates="visit")


# Import here to avoid circular imports
from app.models.assessments import GDMAssessment, AnemiaAssessment, FetalHealthAssessment
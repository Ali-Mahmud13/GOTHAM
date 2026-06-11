"""Assessment models for GDM, Anemia, and Fetal Health predictions."""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime


class GDMAssessment(SQLModel, table=True):
    """Gestational Diabetes Mellitus assessment with risk prediction."""
    
    __tablename__ = "gdm_assessments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    visit_id: int = Field(foreign_key="visits.id", index=True)
    
    # GDM-specific measurements
    glucose_level: Optional[float] = Field(default=None, description="Blood glucose level (mg/dL)")
    blood_pressure_systolic: Optional[int] = Field(default=None, description="Systolic blood pressure (mmHg)")
    blood_pressure_diastolic: Optional[int] = Field(default=None, description="Diastolic blood pressure (mmHg)")
    insulin_level: Optional[float] = Field(default=None, description="Insulin level (μU/mL)")
    bmi: Optional[float] = Field(default=None, description="Body Mass Index")
    hdl: Optional[float] = Field(default=None, description="HDL cholesterol level (mg/dL)")
    ogtt: Optional[float] = Field(default=None, description="Oral glucose tolerance test result (mg/dL)")
    
    # Pregnancy context
    gestation_weeks: Optional[int] = Field(default=None, description="Gestation weeks in current pregnancy")
    sedentary_lifestyle: Optional[bool] = Field(default=None, description="Sedentary lifestyle assessment")
    
    # AI Prediction Results
    risk_level: Optional[int] = Field(default=None, description="Risk level: 0=Normal, 1=Elevated, 2=High")
    confidence: Optional[float] = Field(default=None, description="Model confidence score (0-1)")
    ai_report: Optional[str] = Field(default=None, description="AI-generated risk assessment report")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to visit
    visit: "Visit" = Relationship(back_populates="gdm_assessment")


class AnemiaAssessment(SQLModel, table=True):
    """Anemia assessment based on Complete Blood Count (CBC) parameters."""
    
    __tablename__ = "anemia_assessments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    visit_id: int = Field(foreign_key="visits.id", index=True)
    
    # Complete Blood Count (CBC) Parameters
    wbc: Optional[float] = Field(default=None, description="White Blood Cell count (10⁹/L)")
    rbc: Optional[float] = Field(default=None, description="Red Blood Cell count (10¹²/L)")
    hgb: Optional[float] = Field(default=None, description="Hemoglobin (g/dL)")
    hct: Optional[float] = Field(default=None, description="Hematocrit (%)")
    mcv: Optional[float] = Field(default=None, description="Mean Corpuscular Volume (fL)")
    mch: Optional[float] = Field(default=None, description="Mean Corpuscular Hemoglobin (pg)")
    mchc: Optional[float] = Field(default=None, description="Mean Corpuscular Hemoglobin Concentration (g/dL)")
    plt: Optional[float] = Field(default=None, description="Platelet count (10⁹/L)")
    
    # AI Prediction Results
    diagnosis: Optional[str] = Field(default=None, description="Anemia diagnosis type (e.g., 'Iron deficiency anemia')")
    confidence: Optional[float] = Field(default=None, description="Model confidence score (0-1)")
    ai_report: Optional[str] = Field(default=None, description="AI-generated anemia assessment report")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to visit
    visit: "Visit" = Relationship(back_populates="anemia_assessment")


class FetalHealthAssessment(SQLModel, table=True):
    """Fetal health assessment based on Cardiotocography (CTG) parameters."""
    
    __tablename__ = "fetal_health_assessments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    visit_id: int = Field(foreign_key="visits.id", index=True)
    
    # Cardiotocography (CTG) Parameters
    baseline_value: Optional[float] = Field(default=None, description="Baseline Fetal Heart Rate (bpm)")
    accelerations: Optional[float] = Field(default=None, description="Number of accelerations per second")
    fetal_movement: Optional[float] = Field(default=None, description="Number of fetal movements per second")
    uterine_contractions: Optional[float] = Field(default=None, description="Number of uterine contractions per second")
    light_decelerations: Optional[float] = Field(default=None, description="Number of light decelerations per second")
    severe_decelerations: Optional[float] = Field(default=None, description="Number of severe decelerations per second")
    prolongued_decelerations: Optional[float] = Field(default=None, description="Number of prolonged decelerations per second")
    abnormal_short_term_variability: Optional[float] = Field(default=None, description="% time with abnormal short term variability")
    mean_value_of_short_term_variability: Optional[float] = Field(default=None, description="Mean value of short term variability")
    percentage_of_time_with_abnormal_long_term_variability: Optional[float] = Field(default=None, description="% time with abnormal long term variability")
    mean_value_of_long_term_variability: Optional[float] = Field(default=None, description="Mean value of long term variability")
    
    # Histogram features
    histogram_width: Optional[float] = Field(default=None, description="Width of FHR histogram")
    histogram_min: Optional[float] = Field(default=None, description="Minimum value of FHR histogram")
    histogram_max: Optional[float] = Field(default=None, description="Maximum value of FHR histogram")
    histogram_number_of_peaks: Optional[int] = Field(default=None, description="Number of histogram peaks")
    histogram_number_of_zeroes: Optional[int] = Field(default=None, description="Number of histogram zeros")
    histogram_mode: Optional[float] = Field(default=None, description="Histogram mode")
    histogram_mean: Optional[float] = Field(default=None, description="Histogram mean")
    histogram_median: Optional[float] = Field(default=None, description="Histogram median")
    histogram_variance: Optional[float] = Field(default=None, description="Histogram variance")
    histogram_tendency: Optional[int] = Field(default=None, description="Histogram tendency")
    
    # AI Prediction Results
    status: Optional[int] = Field(default=None, description="Fetal health status: 1=Normal, 2=Suspect, 3=Pathological")
    confidence: Optional[float] = Field(default=None, description="Model confidence score (0-1)")
    ai_report: Optional[str] = Field(default=None, description="AI-generated fetal health assessment report")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to visit
    visit: "Visit" = Relationship(back_populates="fetal_health_assessment")


class MaternalHealthAssessment(SQLModel, table=True):
    """Maternal health / preeclampsia risk assessment."""

    __tablename__ = "maternal_health_assessments"

    id: Optional[int] = Field(default=None, primary_key=True)
    visit_id: int = Field(foreign_key="visits.id", index=True)

    body_temp: Optional[float] = Field(default=None, description="Body temperature (°C)")
    heart_rate: Optional[int] = Field(default=None, description="Heart rate (bpm)")

    risk_level: Optional[int] = Field(default=None, description="Risk level: 0=Low, 1=Mid, 2=High")
    confidence: Optional[float] = Field(default=None, description="Model confidence score (0-1)")
    ai_report: Optional[str] = Field(default=None, description="AI-generated assessment report")

    created_at: datetime = Field(default_factory=datetime.utcnow)

    visit: "Visit" = Relationship(back_populates="maternal_health_assessment")


class UltrasoundImage(SQLModel, table=True):
    """Ultrasound image metadata linked to a visit and patient."""

    __tablename__ = "ultrasound_images"

    id: Optional[int] = Field(default=None, primary_key=True)
    visit_id: int = Field(foreign_key="visits.id", index=True)
    patient_id: int = Field(foreign_key="patients.id", index=True)

    public_id: str = Field(index=True, description="Cloudinary public ID")
    secure_url: str = Field(description="Cloudinary secure URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Cloudinary thumbnail URL")
    file_name: Optional[str] = Field(default=None, description="Original file name")
    format: Optional[str] = Field(default=None, description="Image format from Cloudinary")
    bytes: Optional[int] = Field(default=None, description="File size in bytes")
    width: Optional[int] = Field(default=None)
    height: Optional[int] = Field(default=None)

    uploaded_by_role: Optional[str] = Field(default=None, description="patient or doctor")
    uploaded_by_user_id: Optional[int] = Field(default=None, foreign_key="auth_users.id", index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    visit: "Visit" = Relationship(back_populates="ultrasound_images")

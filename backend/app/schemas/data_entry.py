"""Pydantic schemas for data entry API."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PatientResponse(BaseModel):
    """Patient data for frontend consumption."""
    
    id: str = Field(description="Patient identifier (e.g., P001)")
    name: Optional[str] = Field(default="Patient", description="Patient name if available")
    age: Optional[int] = Field(default=None, description="Patient age from latest visit")
    gestational_age: Optional[str] = Field(default=None, description="Current gestational age")
    last_visit: Optional[str] = Field(default="Never", description="Relative time of last visit")
    risk_level: str = Field(
        default="unassessed",
        description="Risk level: unassessed, low, medium, high",
    )
    
    class Config:
        """Pydantic config."""
        from_attributes = True
        populate_by_name = True
        
        # Convert snake_case to camelCase for frontend
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word 
            for i, word in enumerate(field_name.split('_'))
        )
        by_alias = True


class ExtractedField(BaseModel):
    """A single extracted field from clinical notes."""
    
    name: str = Field(description="Field name (e.g., 'BMI', 'Blood Pressure')")
    value: bool | int | float | str = Field(description="Extracted value")
    confidence: str = Field(description="Confidence level: high, medium, low")
    db_field: Optional[str] = Field(default=None, description="Database field name for mapping", alias="dbField")
    
    class Config:
        populate_by_name = True  # Allow both db_field and dbField


class MissingField(BaseModel):
    """A required field that wasn't found in the notes."""
    
    name: str = Field(description="Missing field name")
    category: str = Field(description="Category (e.g., 'Lab Results', 'Vitals')")
    db_field: str = Field(description="Database field name")


class NotesParseRequest(BaseModel):
    """Request to parse clinical notes."""
    
    notes: str = Field(description="Clinical notes text")
    patient_id: Optional[str] = Field(default=None, description="Patient identifier for context")


class NotesParseResponse(BaseModel):
    """Response with extracted data from clinical notes."""
    
    extracted_fields: List[ExtractedField] = Field(description="Successfully extracted fields")
    missing_fields: List[MissingField] = Field(description="Required fields not found in notes")
    success: bool = Field(description="Whether parsing was successful")
    message: Optional[str] = Field(default=None, description="Additional info or errors")


class CreateVisitRequest(BaseModel):
    """Request to create a new visit record."""
    
    patient_id: str = Field(description="Patient identifier")
    visit_type: str = Field(default="clinical_notes", description="Type of visit")
    
    # GDM Assessment fields
    glucose_level: Optional[float] = None  # Blood glucose (different from OGTT)
    gestation_weeks: Optional[int] = None  # Current gestation weeks
    bmi: Optional[float] = None
    sys_bp: Optional[int] = None
    dia_bp: Optional[int] = None
    hdl: Optional[float] = None
    ogtt: Optional[float] = None
    sedentary_lifestyle: Optional[bool] = None
    
    # Anemia/CBC Assessment fields (Complete Blood Count)
    wbc: Optional[float] = None  # White Blood Cell count (10⁹/L)
    rbc: Optional[float] = None  # Red Blood Cell count (10¹²/L)
    hgb: Optional[float] = None  # Hemoglobin (g/dL) - renamed from hemoglobin
    hct: Optional[float] = None  # Hematocrit (%)
    mcv: Optional[float] = None  # Mean Corpuscular Volume (fL)
    mch: Optional[float] = None  # Mean Corpuscular Hemoglobin (pg)
    mchc: Optional[float] = None  # Mean Corpuscular Hemoglobin Concentration (g/dL)
    plt: Optional[float] = None  # Platelet count (10⁹/L)
    
    # GDM additional
    insulin_level: Optional[float] = None  # Insulin level (μU/mL)

    # Preeclampsia / Maternal Health model
    body_temp: Optional[float] = None   # Body temperature (°C)
    heart_rate: Optional[int] = None    # Heart rate (bpm)

    # Fetal Health/CTG Assessment fields (all 21)
    baseline_value: Optional[float] = None  # Baseline Fetal Heart Rate (bpm)
    accelerations: Optional[float] = None  # Accelerations per second
    fetal_movement: Optional[float] = None  # Fetal movements per second
    uterine_contractions: Optional[float] = None  # Uterine contractions per second
    light_decelerations: Optional[float] = None
    severe_decelerations: Optional[float] = None
    prolongued_decelerations: Optional[float] = None
    abnormal_short_term_variability: Optional[float] = None  # % time
    mean_value_of_short_term_variability: Optional[float] = None
    percentage_of_time_with_abnormal_long_term_variability: Optional[float] = None  # %
    mean_value_of_long_term_variability: Optional[float] = None
    histogram_width: Optional[float] = None
    histogram_min: Optional[float] = None
    histogram_max: Optional[float] = None
    histogram_number_of_peaks: Optional[int] = None
    histogram_number_of_zeroes: Optional[int] = None
    histogram_mode: Optional[float] = None
    histogram_mean: Optional[float] = None
    histogram_median: Optional[float] = None
    histogram_variance: Optional[float] = None
    histogram_tendency: Optional[int] = None

    # Pregnancy history
    no_of_pregnancy: Optional[int] = None
    gestation_in_previous_pregnancy: Optional[int] = None
    
    # Static patient features (will update patient record if provided)
    family_history: Optional[bool] = None
    pcos: Optional[bool] = None
    unexplained_prenatal_loss: Optional[bool] = None
    large_child_or_birth_default: Optional[bool] = None
    prediabetes: Optional[bool] = None
    
    notes: Optional[str] = Field(default=None, description="Clinical notes")


class VisitResponse(BaseModel):
    """Response after creating a visit."""
    
    visit_id: int = Field(description="Created visit ID")
    patient_id: str = Field(description="Patient identifier")
    visit_date: datetime = Field(description="Visit timestamp")
    success: bool = Field(description="Whether creation was successful")
    message: str = Field(description="Success or error message")


class UltrasoundImageResponse(BaseModel):
    """Ultrasound image payload for frontend and ML references."""

    id: int
    visit_id: int
    patient_id: int
    public_id: str
    secure_url: str
    thumbnail_url: Optional[str] = None
    file_name: Optional[str] = None
    format: Optional[str] = None
    bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    uploaded_by_role: Optional[str] = None
    uploaded_by_user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UltrasoundUploadResponse(BaseModel):
    """Response payload after uploading one or more ultrasound images."""

    success: bool
    message: str
    uploaded: List[UltrasoundImageResponse] = Field(default_factory=list)


class UltrasoundDeleteResponse(BaseModel):
    """Response payload after deleting an ultrasound image."""

    success: bool
    message: str

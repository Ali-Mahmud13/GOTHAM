"""
Materialized view for latest patient assessment data.

This table is automatically maintained by PostgreSQL triggers.
DO NOT update directly from application code.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class PatientLatestAssessments(SQLModel, table=True):
    """
    Stores the latest non-null value for each assessment field across all visits.
    
    Updated automatically by database triggers on INSERT/UPDATE to:
    - gdm_assessments
    - anemia_assessments
    - fetal_health_assessments
    
    Performance: Enables 2-query patient data retrieval instead of 13+
    """
    __tablename__ = "patient_latest_assessments"
    
    patient_id: int = Field(primary_key=True, foreign_key="patients.id")
    
    # ============ GDM FIELDS ============
    glucose_level: Optional[float] = None
    glucose_updated_at: Optional[datetime] = None
    
    sys_bp: Optional[int] = None
    sys_bp_updated_at: Optional[datetime] = None
    
    dia_bp: Optional[int] = None
    dia_bp_updated_at: Optional[datetime] = None
    
    bmi: Optional[float] = None
    bmi_updated_at: Optional[datetime] = None
    
    ogtt: Optional[float] = None
    ogtt_updated_at: Optional[datetime] = None
    
    hdl: Optional[float] = None
    hdl_updated_at: Optional[datetime] = None
    
    gestation_weeks: Optional[int] = None
    gestation_weeks_updated_at: Optional[datetime] = None
    
    sedentary_lifestyle: Optional[bool] = None
    sedentary_lifestyle_updated_at: Optional[datetime] = None
    
    insulin_level: Optional[float] = None
    insulin_level_updated_at: Optional[datetime] = None
    
    # ============ ANEMIA/CBC FIELDS ============
    wbc: Optional[float] = None
    wbc_updated_at: Optional[datetime] = None
    
    rbc: Optional[float] = None
    rbc_updated_at: Optional[datetime] = None
    
    hgb: Optional[float] = None
    hgb_updated_at: Optional[datetime] = None
    
    hct: Optional[float] = None
    hct_updated_at: Optional[datetime] = None
    
    mcv: Optional[float] = None
    mcv_updated_at: Optional[datetime] = None
    
    mch: Optional[float] = None
    mch_updated_at: Optional[datetime] = None
    
    mchc: Optional[float] = None
    mchc_updated_at: Optional[datetime] = None
    
    plt: Optional[float] = None
    plt_updated_at: Optional[datetime] = None
    
    # ============ FETAL HEALTH FIELDS ============
    # Baseline and movements
    fetal_baseline_value: Optional[float] = None
    fetal_baseline_updated_at: Optional[datetime] = None
    
    fetal_accelerations: Optional[float] = None
    fetal_accelerations_updated_at: Optional[datetime] = None
    
    fetal_movement: Optional[float] = None
    fetal_movement_updated_at: Optional[datetime] = None
    
    # Contractions and decelerations
    uterine_contractions: Optional[float] = None
    uterine_contractions_updated_at: Optional[datetime] = None
    
    light_decelerations: Optional[float] = None
    light_decelerations_updated_at: Optional[datetime] = None
    
    severe_decelerations: Optional[float] = None
    severe_decelerations_updated_at: Optional[datetime] = None
    
    prolongued_decelerations: Optional[float] = None
    prolongued_decelerations_updated_at: Optional[datetime] = None
    
    # Variability measures
    abnormal_short_term_variability: Optional[float] = None
    abnormal_short_term_variability_updated_at: Optional[datetime] = None
    
    mean_value_of_short_term_variability: Optional[float] = None
    mean_value_of_short_term_variability_updated_at: Optional[datetime] = None
    
    percentage_of_time_with_abnormal_long_term_variability: Optional[float] = None
    percentage_of_time_with_abnormal_long_term_variability_updated_at: Optional[datetime] = None
    
    mean_value_of_long_term_variability: Optional[float] = None
    mean_value_of_long_term_variability_updated_at: Optional[datetime] = None
    
    # Histogram fields
    histogram_width: Optional[float] = None
    histogram_width_updated_at: Optional[datetime] = None
    
    histogram_min: Optional[float] = None
    histogram_min_updated_at: Optional[datetime] = None
    
    histogram_max: Optional[float] = None
    histogram_max_updated_at: Optional[datetime] = None
    
    histogram_number_of_peaks: Optional[int] = None
    histogram_number_of_peaks_updated_at: Optional[datetime] = None
    
    histogram_number_of_zeroes: Optional[int] = None
    histogram_number_of_zeroes_updated_at: Optional[datetime] = None
    
    histogram_mode: Optional[float] = None
    histogram_mode_updated_at: Optional[datetime] = None
    
    histogram_mean: Optional[float] = None
    histogram_mean_updated_at: Optional[datetime] = None
    
    histogram_median: Optional[float] = None
    histogram_median_updated_at: Optional[datetime] = None
    
    histogram_variance: Optional[float] = None
    histogram_variance_updated_at: Optional[datetime] = None
    
    histogram_tendency: Optional[int] = None
    histogram_tendency_updated_at: Optional[datetime] = None
    
    # ============ METADATA ============
    last_updated: datetime = Field(default_factory=datetime.utcnow)

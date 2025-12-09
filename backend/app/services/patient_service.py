"""Patient service - Handles patient data fetching and management."""

from typing import Dict, Optional, List
from sqlmodel import Session, select
from app.db.session import engine
from app.models import Patient, Visit, GDMAssessment, AnemiaAssessment, FetalHealthAssessment
import logging

logger = logging.getLogger(__name__)


class PatientService:
    """Service class for managing patient data via database."""
    
    def __init__(self):
        """Initialize the patient service."""
        logger.info("Patient service initialized with database connection")
    
    async def get_patient_data(self, patient_identifier: str) -> Dict:
        """
        Fetch patient data by patient ID, including latest visit and assessments.
        
        Args:
            patient_identifier: The patient ID to search for
            
        Returns:
            Dictionary containing patient data with latest assessments
        """
        try:
            logger.info(f"Fetching data for patient: {patient_identifier}")
            
            with Session(engine) as session:
                # Fetch patient
                statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
                patient = session.exec(statement).first()
                
                if not patient:
                    logger.warning(f"No patient found with identifier: {patient_identifier}")
                    return {}
                
                logger.info(f"Found patient: {patient.name} (ID: {patient.id})")
                
                # Fetch ALL visits (newest to oldest) for field-level aggregation
                visit_statement = (
                    select(Visit)
                    .where(Visit.patient_id == patient.id)
                    .order_by(Visit.visit_date.desc())
                )
                all_visits = session.exec(visit_statement).all()
                
                if all_visits:
                    logger.info(f"Found {len(all_visits)} visits for patient (latest: {all_visits[0].visit_date})")
                else:
                    logger.info("No visits found for patient")
                
                # Build response with field-level aggregation across all visits
                try:
                    patient_data = self._build_patient_response(patient, all_visits, session)
                    logger.info(f"Successfully built patient response with {len(patient_data)} fields")
                except Exception as build_error:
                    logger.error(f"Error building patient response: {str(build_error)}", exc_info=True)
                    return {}
                
                # Commit to ensure all data is loaded
                session.commit()
                
                logger.info(f"Patient data retrieved successfully for: {patient_identifier}")
                return patient_data
                
        except Exception as e:
            logger.error(f"Error fetching patient data: {str(e)}", exc_info=True)
            return {}
    
    async def validate_patient_id(self, patient_identifier: str) -> bool:
        """
        Check if a patient ID exists in the database.
        
        Args:
            patient_identifier: The patient ID to validate
            
        Returns:
            True if patient exists, False otherwise
        """
        try:
            with Session(engine) as session:
                statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
                patient = session.exec(statement).first()
                return patient is not None
        except Exception as e:
            logger.error(f"Error validating patient ID: {str(e)}")
            return False
    
    async def get_patient_visit_history(self, patient_identifier: str) -> List[Dict]:
        """
        Get all visits for a patient with assessments.
        
        Args:
            patient_identifier: The patient ID
            
        Returns:
            List of visit dictionaries with assessments
        """
        try:
            with Session(engine) as session:
                # Get patient
                statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
                patient = session.exec(statement).first()
                
                if not patient:
                    logger.warning(f"No patient found with identifier: {patient_identifier}")
                    return []
                
                # Get all visits
                visits_statement = (
                    select(Visit)
                    .where(Visit.patient_id == patient.id)
                    .order_by(Visit.visit_date.desc())
                )
                visits = session.exec(visits_statement).all()
                
                return [self._build_visit_dict(visit, session) for visit in visits]
                
        except Exception as e:
            logger.error(f"Error fetching visit history: {str(e)}", exc_info=True)
            return []
    
    def _build_patient_response(self, patient: Patient, visits: List[Visit], session: Session) -> Dict:
        """
        Build patient data response dictionary with field-level aggregation across all visits.
        
        For each assessment field, uses the latest non-null value across all visits.
        This ensures complete data even when doctors enter partial information per visit.
        
        Args:
            patient: Patient model instance
            visits: List of Visit instances (ordered newest to oldest)
            session: Database session for querying assessments
            
        Returns:
            Dictionary with patient data and aggregated assessment fields
        """
        response = {
            # Patient identifier
            "Patient_ID": patient.patient_identifier,
            "name": patient.name,
            "age": patient.age,
            "contact_number": patient.contact_number,
            "risk_level": patient.risk_level,
            
            # Static medical history (boolean features for GDM model)
            "family_history": patient.family_history,
            "pcos": patient.pcos,
            "unexplained_prenatal_loss": patient.unexplained_prenatal_loss,
            "large_child_or_birth_default": patient.large_child_or_birth_default,
            "prediabetes": patient.prediabetes,
            
            # Using ML model field names
            "no_of_pregnancy": patient.number_of_pregnancies,
            "bmi_category": patient.bmi_category,
            
            # Smart defaults for fields not in Patient model
            # Gestation in previous pregnancy: 0 for first pregnancy, 38 weeks (full term) for subsequent
            "gestation_in_previous_pregnancy": 0 if patient.number_of_pregnancies == 1 else 38,
            # Sedentary lifestyle: Default to False (assume not sedentary unless documented)
            "sedentary_lifestyle": False,
            # HDL: Default to 50 mg/dL (mid-range normal for women: 40-60 mg/dL)
            "hdl": 50.0,
            # Hemoglobin: Default to 12.0 g/dL (normal range for pregnant women: 11-14 g/dL)
            "hemoglobin": 12.0,
        }
        
        # Add visit metadata from latest visit if available
        if visits:
            latest_visit = visits[0]  # Already sorted newest first
            response["visit_date"] = latest_visit.visit_date.isoformat()
            response["visit_type"] = latest_visit.visit_type
            response["visit_notes"] = latest_visit.notes
            
            # Aggregate assessments across all visits
            merged_gdm = self._merge_gdm_assessments(visits, session)
            merged_anemia = self._merge_anemia_assessments(visits, session)
            merged_fetal = self._merge_fetal_assessments(visits, session)
            
            # Add merged GDM data
            if merged_gdm:
                response.update(merged_gdm)
            
            # Add merged Anemia data
            if merged_anemia:
                response.update(merged_anemia)
            
            # Add merged Fetal Health data
            if merged_fetal:
                response.update(merged_fetal)
        
        return response
    
    def _merge_gdm_assessments(self, visits: List[Visit], session: Session) -> Dict:
        """
        Merge GDM assessment data across all visits, taking latest non-null value per field.
        
        Args:
            visits: List of visits (newest to oldest)
            session: Database session
            
        Returns:
            Dictionary with merged GDM fields
        """
        merged = {}
        
        for visit in visits:
            gdm = session.exec(
                select(GDMAssessment).where(GDMAssessment.visit_id == visit.id)
            ).first()
            
            if not gdm:
                continue
            
            # For each field, use first non-null value encountered (newest first)
            if "glucose_level" not in merged and gdm.glucose_level is not None:
                merged["glucose_level"] = gdm.glucose_level
            if "gestation_weeks" not in merged and gdm.gestation_weeks is not None:
                merged["gestation_weeks"] = gdm.gestation_weeks
            if "gdm_risk_level" not in merged and gdm.risk_level is not None:
                merged["gdm_risk_level"] = gdm.risk_level
            if "gdm_confidence" not in merged and gdm.confidence is not None:
                merged["gdm_confidence"] = gdm.confidence
            if "sys_bp" not in merged and gdm.blood_pressure_systolic is not None:
                merged["sys_bp"] = gdm.blood_pressure_systolic
            if "dia_bp" not in merged and gdm.blood_pressure_diastolic is not None:
                merged["dia_bp"] = gdm.blood_pressure_diastolic
            if "bmi" not in merged and gdm.bmi is not None:
                merged["bmi"] = gdm.bmi
            if "ogtt" not in merged and gdm.ogtt is not None:
                merged["ogtt"] = gdm.ogtt
            if "hdl" not in merged and gdm.hdl is not None:
                merged["hdl"] = gdm.hdl
            if "insulin_level" not in merged and gdm.insulin_level is not None:
                merged["insulin_level"] = gdm.insulin_level
            if "sedentary_lifestyle" not in merged and gdm.sedentary_lifestyle is not None:
                merged["sedentary_lifestyle"] = gdm.sedentary_lifestyle
        
        return merged
    
    def _merge_anemia_assessments(self, visits: List[Visit], session: Session) -> Dict:
        """
        Merge Anemia/CBC assessment data across all visits, taking latest non-null value per field.
        
        Args:
            visits: List of visits (newest to oldest)
            session: Database session
            
        Returns:
            Dictionary with merged Anemia fields
        """
        merged = {}
        
        for visit in visits:
            anemia = session.exec(
                select(AnemiaAssessment).where(AnemiaAssessment.visit_id == visit.id)
            ).first()
            
            if not anemia:
                continue
            
            # For each field, use first non-null value encountered
            if "anemia_diagnosis" not in merged and anemia.diagnosis is not None:
                merged["anemia_diagnosis"] = anemia.diagnosis
            if "anemia_confidence" not in merged and anemia.confidence is not None:
                merged["anemia_confidence"] = anemia.confidence
            
            # CBC parameters (uppercase for ML models)
            if "WBC" not in merged and anemia.wbc is not None:
                merged["WBC"] = anemia.wbc
            if "RBC" not in merged and anemia.rbc is not None:
                merged["RBC"] = anemia.rbc
            if "HGB" not in merged and anemia.hgb is not None:
                merged["HGB"] = anemia.hgb
                merged["hemoglobin"] = anemia.hgb  # Also add lowercase for compatibility
            if "HCT" not in merged and anemia.hct is not None:
                merged["HCT"] = anemia.hct
            if "MCV" not in merged and anemia.mcv is not None:
                merged["MCV"] = anemia.mcv
            if "MCH" not in merged and anemia.mch is not None:
                merged["MCH"] = anemia.mch
            if "MCHC" not in merged and anemia.mchc is not None:
                merged["MCHC"] = anemia.mchc
            if "PLT" not in merged and anemia.plt is not None:
                merged["PLT"] = anemia.plt
        
        return merged
    
    def _merge_fetal_assessments(self, visits: List[Visit], session: Session) -> Dict:
        """
        Merge Fetal Health assessment data across all visits, taking latest non-null value per field.
        
        Args:
            visits: List of visits (newest to oldest)
            session: Database session
            
        Returns:
            Dictionary with merged Fetal Health fields
        """
        merged = {}
        
        for visit in visits:
            fhp = session.exec(
                select(FetalHealthAssessment).where(FetalHealthAssessment.visit_id == visit.id)
            ).first()
            
            if not fhp:
                continue
            
            # For each field, use first non-null value encountered
            if "fetal_heart_rate_baseline" not in merged and fhp.baseline_value is not None:
                merged["fetal_heart_rate_baseline"] = fhp.baseline_value
            if "fetal_accelerations" not in merged and fhp.accelerations is not None:
                merged["fetal_accelerations"] = fhp.accelerations
            if "fetal_movement" not in merged and fhp.fetal_movement is not None:
                merged["fetal_movement"] = fhp.fetal_movement
            if "fetal_status" not in merged and fhp.status is not None:
                merged["fetal_status"] = fhp.status
            if "fetal_confidence" not in merged and fhp.confidence is not None:
                merged["fetal_confidence"] = fhp.confidence
        
        return merged
    
    def _build_visit_dict(self, visit: Visit, session: Session) -> Dict:
        """
        Build visit dictionary with all assessments.
        
        Args:
            visit: Visit model instance
            session: Database session
            
        Returns:
            Dictionary with visit and assessment data
        """
        visit_dict = {
            "visit_id": visit.id,
            "visit_date": visit.visit_date.isoformat(),
            "visit_type": visit.visit_type,
            "notes": visit.notes,
        }
        
        # Add assessments
        gdm = session.exec(select(GDMAssessment).where(GDMAssessment.visit_id == visit.id)).first()
        anemia = session.exec(select(AnemiaAssessment).where(AnemiaAssessment.visit_id == visit.id)).first()
        fhp = session.exec(select(FetalHealthAssessment).where(FetalHealthAssessment.visit_id == visit.id)).first()
        
        if gdm:
            visit_dict["gdm"] = {
                "glucose": gdm.glucose_level,
                "bp_systolic": gdm.blood_pressure_systolic,
                "bp_diastolic": gdm.blood_pressure_diastolic,
                "bmi": gdm.bmi,
                "risk_level": gdm.risk_level,
            }
        
        if anemia:
            visit_dict["anemia"] = {
                "hemoglobin": anemia.hgb,
                "diagnosis": anemia.diagnosis,
            }
        
        if fhp:
            visit_dict["fetal_health"] = {
                "baseline_fhr": fhp.baseline_value,
                "status": fhp.status,
            }
        
        return visit_dict


# Singleton instance
_patient_service_instance = None


def get_patient_service() -> PatientService:
    """
    Get the singleton patient service instance.
    
    Returns:
        PatientService instance
    """
    global _patient_service_instance
    if _patient_service_instance is None:
        _patient_service_instance = PatientService()
    return _patient_service_instance

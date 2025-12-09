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
                
                # Fetch latest visit
                visit_statement = (
                    select(Visit)
                    .where(Visit.patient_id == patient.id)
                    .order_by(Visit.visit_date.desc())
                )
                latest_visit = session.exec(visit_statement).first()
                
                if latest_visit:
                    logger.info(f"Found latest visit: {latest_visit.visit_date}")
                else:
                    logger.info("No visits found for patient")
                
                # Build response - this accesses all relationships
                try:
                    patient_data = self._build_patient_response(patient, latest_visit, session)
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
    
    def _build_patient_response(self, patient: Patient, latest_visit: Optional[Visit], session: Session) -> Dict:
        """
        Build patient data response dictionary compatible with agent's expected format.
        
        Args:
            patient: Patient model instance
            latest_visit: Optional latest Visit instance
            session: Database session for querying assessments
            
        Returns:
            Dictionary with patient data and latest assessments
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
        
        # Add latest visit data if available
        if latest_visit:
            response["visit_date"] = latest_visit.visit_date.isoformat()
            response["visit_type"] = latest_visit.visit_type
            response["visit_notes"] = latest_visit.notes
            
            # Fetch latest assessments for this visit
            gdm = session.exec(
                select(GDMAssessment).where(GDMAssessment.visit_id == latest_visit.id)
            ).first()
            
            anemia = session.exec(
                select(AnemiaAssessment).where(AnemiaAssessment.visit_id == latest_visit.id)
            ).first()
            
            fhp = session.exec(
                select(FetalHealthAssessment).where(FetalHealthAssessment.visit_id == latest_visit.id)
            ).first()
            
            # Add GDM data if available (using ML model field names)
            if gdm:
                response.update({
                    # For display/logging
                    "glucose_level": gdm.glucose_level,
                    "gestation_weeks": gdm.gestation_weeks,
                    "gdm_risk_level": gdm.risk_level,
                    "gdm_confidence": gdm.confidence,
                    # For ML models (using contract field names)
                    "sys_bp": gdm.blood_pressure_systolic,
                    "dia_bp": gdm.blood_pressure_diastolic,
                    "bmi": gdm.bmi,
                    "ogtt": gdm.ogtt,
                })
            
            # Add Anemia data if available (using ML model field names)
            if anemia:
                response.update({
                    # For display/logging
                    "anemia_diagnosis": anemia.diagnosis,
                    "anemia_confidence": anemia.confidence,
                    # For ML models (using contract field names - uppercase)
                    "WBC": anemia.wbc,
                    "RBC": anemia.rbc,
                    "HGB": anemia.hgb,
                    "HCT": anemia.hct,
                    "MCV": anemia.mcv,
                    "MCH": anemia.mch,
                    "MCHC": anemia.mchc,
                    "PLT": anemia.plt,
                    # Also lowercase for backward compatibility
                    "hemoglobin": anemia.hgb,
                })
            
            # Add Fetal Health data if available
            if fhp:
                response.update({
                    "fetal_heart_rate_baseline": fhp.baseline_value,
                    "fetal_accelerations": fhp.accelerations,
                    "fetal_status": fhp.status,
                    "fetal_confidence": fhp.confidence,
                })
        
        return response
    
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

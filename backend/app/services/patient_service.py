"""Patient service - Handles patient data fetching and management."""

from typing import Dict, Optional
from sqlmodel import Session
from app.db.session import engine
from app.repositories import PatientRepository, VisitRepository
import logging

logger = logging.getLogger(__name__)


class PatientService:
    """Service class for managing patient data via database using repository pattern."""
    
    def __init__(self):
        """Initialize the patient service."""
        logger.info("Patient service initialized with database connection")
    
    def _get_repositories(self, session: Session) -> tuple[PatientRepository, VisitRepository]:
        """
        Get repository instances for a session.
        
        Args:
            session: Database session
            
        Returns:
            Tuple of (PatientRepository, VisitRepository)
        """
        return PatientRepository(session), VisitRepository(session)
    
    async def get_patient_data(self, patient_identifier: str) -> Dict:
        """
        Fetch patient data by patient ID, combining static features with latest visit data.
        
        Args:
            patient_identifier: The patient ID to search for
            
        Returns:
            Dictionary containing combined patient and latest visit data, or empty dict if not found
        """
        try:
            logger.info(f"Fetching data for patient: {patient_identifier}")
            
            with Session(engine) as session:
                patient_repo, visit_repo = self._get_repositories(session)
                
                # Fetch patient with static features
                patient = patient_repo.get_by_identifier(patient_identifier)
                
                if not patient:
                    logger.warning(f"No patient found with identifier: {patient_identifier}")
                    return {}
                
                # Fetch latest visit for this patient
                latest_visit = visit_repo.get_latest_for_patient(patient.id)
                
                # Combine patient and visit data
                patient_data = self._build_patient_response(patient, latest_visit)
                
                if latest_visit:
                    logger.info(f"Patient data with latest visit from {latest_visit.visit_date} retrieved successfully")
                else:
                    logger.info(f"Patient found but no visits recorded yet")
                
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
                patient_repo, _ = self._get_repositories(session)
                return patient_repo.exists(patient_identifier)
        except Exception as e:
            logger.error(f"Error validating patient ID: {str(e)}")
            return False
    
    async def get_patient_visit_history(self, patient_identifier: str) -> list[Dict]:
        """
        Get all visits for a patient, ordered by date (most recent first).
        
        Args:
            patient_identifier: The patient ID
            
        Returns:
            List of visit dictionaries
        """
        try:
            with Session(engine) as session:
                patient_repo, visit_repo = self._get_repositories(session)
                
                # Get patient
                patient = patient_repo.get_by_identifier(patient_identifier)
                
                if not patient:
                    logger.warning(f"No patient found with identifier: {patient_identifier}")
                    return []
                
                # Get all visits
                visits = visit_repo.get_all_for_patient(patient.id)
                
                return [self._build_visit_response(visit) for visit in visits]
                
        except Exception as e:
            logger.error(f"Error fetching visit history: {str(e)}", exc_info=True)
            return []
    
    def _build_patient_response(self, patient, latest_visit=None) -> Dict:
        """
        Build patient data response dictionary.
        
        Args:
            patient: Patient model instance
            latest_visit: Optional latest Visit model instance
            
        Returns:
            Dictionary with patient and visit data
        """
        response = {
            "Patient_ID": patient.patient_identifier,
            "family_history": patient.family_history,
            "pcos": patient.pcos,
            "unexplained_prenatal_loss": patient.unexplained_prenatal_loss,
            "large_child_or_birth_default": patient.large_child_or_birth_default,
            "prediabetes": patient.prediabetes,
        }
        
        if latest_visit:
            response.update(self._build_visit_response(latest_visit))
        
        return response
    
    def _build_visit_response(self, visit) -> Dict:
        """
        Build visit data response dictionary.
        
        Args:
            visit: Visit model instance
            
        Returns:
            Dictionary with visit data
        """
        return {
            "age": visit.age,
            "bmi": visit.bmi,
            "sys_bp": visit.sys_bp,
            "dia_bp": visit.dia_bp,
            "hdl": visit.hdl,
            "hemoglobin": visit.hemoglobin,
            "ogtt": visit.ogtt,
            "no_of_pregnancy": visit.no_of_pregnancy,
            "gestation_in_previous_pregnancy": visit.gestation_in_previous_pregnancy,
            "sedentary_lifestyle": visit.sedentary_lifestyle,
            "visit_date": visit.visit_date.isoformat() if visit.visit_date else None,
        }


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





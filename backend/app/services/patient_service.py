"""Patient service - Handles patient data fetching and management."""

from typing import Dict, Optional
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PatientService:
    """Service class for managing patient data."""
    
    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize the patient service.
        
        Args:
            data_path: Optional path to the patient data CSV file
        """
        if data_path is None:
            # Default to data_temp location for now
            # TODO: Move data to a proper location (e.g., /data directory)
            data_path = Path(__file__).parent.parent / "agent" / "data_temp" / "data.csv"
        
        self.data_path = data_path
        logger.info(f"Patient service initialized with data path: {data_path}")
    
    async def get_patient_data(self, patient_identifier: str) -> Dict:
        """
        Fetch patient data by patient ID.
        
        Args:
            patient_identifier: The patient ID to search for
            
        Returns:
            Dictionary containing patient data, or empty dict if not found
        """
        try:
            logger.info(f"Fetching data for patient: {patient_identifier}")
            
            # Read the CSV file
            df = pd.read_csv(self.data_path)
            
            # Search for patient by ID
            patient_row = df[
                (df['Patient_ID'].astype(str) == str(patient_identifier))
            ]
            
            if patient_row.empty:
                logger.warning(f"No data found for patient: {patient_identifier}")
                return {}
            
            # Convert to dictionary
            patient_data = patient_row.iloc[0].to_dict()
            logger.info(f"Patient data retrieved successfully for: {patient_identifier}")
            
            return patient_data
            
        except FileNotFoundError:
            logger.error(f"Patient data file not found: {self.data_path}")
            return {}
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
            df = pd.read_csv(self.data_path)
            patient_exists = (df['Patient_ID'].astype(str) == str(patient_identifier)).any()
            return patient_exists
        except Exception as e:
            logger.error(f"Error validating patient ID: {str(e)}")
            return False


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



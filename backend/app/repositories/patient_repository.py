"""Database repository pattern for clean data access layer."""

from typing import Optional, List
from sqlmodel import Session, select
from app.models import Patient, Visit
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PatientRepository:
    """Repository for Patient database operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLModel database session
        """
        self.session = session
    
    def get_by_identifier(self, patient_identifier: str) -> Optional[Patient]:
        """
        Get patient by their identifier.
        
        Args:
            patient_identifier: Patient's unique identifier
            
        Returns:
            Patient object or None if not found
        """
        statement = select(Patient).where(Patient.patient_identifier == patient_identifier)
        return self.session.exec(statement).first()
    
    def get_by_id(self, patient_id: int) -> Optional[Patient]:
        """
        Get patient by database ID.
        
        Args:
            patient_id: Patient's database ID
            
        Returns:
            Patient object or None if not found
        """
        statement = select(Patient).where(Patient.id == patient_id)
        return self.session.exec(statement).first()
    
    def create(self, patient_data: dict) -> Patient:
        """
        Create a new patient record.
        
        Args:
            patient_data: Dictionary containing patient attributes
            
        Returns:
            Created Patient object
        """
        patient = Patient(**patient_data)
        self.session.add(patient)
        self.session.commit()
        self.session.refresh(patient)
        return patient
    
    def update(self, patient: Patient) -> Patient:
        """
        Update existing patient record.
        
        Args:
            patient: Patient object with updated data
            
        Returns:
            Updated Patient object
        """
        patient.updated_at = datetime.utcnow()
        self.session.add(patient)
        self.session.commit()
        self.session.refresh(patient)
        return patient
    
    def exists(self, patient_identifier: str) -> bool:
        """
        Check if patient exists by identifier.
        
        Args:
            patient_identifier: Patient's unique identifier
            
        Returns:
            True if patient exists, False otherwise
        """
        return self.get_by_identifier(patient_identifier) is not None


class VisitRepository:
    """Repository for Visit database operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLModel database session
        """
        self.session = session
    
    def get_latest_for_patient(self, patient_id: int) -> Optional[Visit]:
        """
        Get the most recent visit for a patient.
        
        Args:
            patient_id: Patient's database ID
            
        Returns:
            Latest Visit object or None if no visits exist
        """
        statement = (
            select(Visit)
            .where(Visit.patient_id == patient_id)
            .order_by(Visit.visit_date.desc())
        )
        return self.session.exec(statement).first()
    
    def get_all_for_patient(self, patient_id: int) -> List[Visit]:
        """
        Get all visits for a patient, ordered by date (most recent first).
        
        Args:
            patient_id: Patient's database ID
            
        Returns:
            List of Visit objects
        """
        statement = (
            select(Visit)
            .where(Visit.patient_id == patient_id)
            .order_by(Visit.visit_date.desc())
        )
        return list(self.session.exec(statement).all())
    
    def create(self, visit_data: dict) -> Visit:
        """
        Create a new visit record.
        
        Args:
            visit_data: Dictionary containing visit attributes
            
        Returns:
            Created Visit object
        """
        visit = Visit(**visit_data)
        self.session.add(visit)
        self.session.commit()
        self.session.refresh(visit)
        return visit
    
    def update(self, visit: Visit) -> Visit:
        """
        Update existing visit record.
        
        Args:
            visit: Visit object with updated data
            
        Returns:
            Updated Visit object
        """
        visit.updated_at = datetime.utcnow()
        self.session.add(visit)
        self.session.commit()
        self.session.refresh(visit)
        return visit

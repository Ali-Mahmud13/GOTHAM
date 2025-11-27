"""Data entry service - Handles clinical notes parsing and visit creation."""

from typing import List, Dict
from sqlmodel import Session
from datetime import datetime, timedelta
from app.repositories import PatientRepository, VisitRepository
from app.schemas import (
    PatientResponse,
    ExtractedField,
    MissingField,
    NotesParseResponse,
    CreateVisitRequest,
    VisitResponse,
)
from app.core.llm import get_llm
from langchain_core.messages import HumanMessage
import logging
import json

logger = logging.getLogger(__name__)


class DataEntryService:
    """Service for data entry operations."""
    
    def __init__(self, session: Session):
        """
        Initialize service with database session.
        
        Args:
            session: SQLModel database session
        """
        self.session = session
        self.patient_repo = PatientRepository(session)
        self.visit_repo = VisitRepository(session)
    
    def get_all_patients(self) -> List[PatientResponse]:
        """
        Get all patients with their latest visit info.
        
        Returns:
            List of PatientResponse objects
        """
        try:
            from app.models import Patient
            
            patients = self.session.query(Patient).all()
            patient_responses = []
            
            for patient in patients:
                # Get latest visit
                latest_visit = self.visit_repo.get_latest_for_patient(patient.id)
                
                # Calculate relative last visit time
                last_visit_str = "Never"
                if latest_visit:
                    delta = datetime.utcnow() - latest_visit.visit_date
                    if delta.days == 0:
                        last_visit_str = "Today"
                    elif delta.days == 1:
                        last_visit_str = "Yesterday"
                    elif delta.days < 7:
                        last_visit_str = f"{delta.days} days ago"
                    elif delta.days < 30:
                        weeks = delta.days // 7
                        last_visit_str = f"{weeks} week{'s' if weeks > 1 else ''} ago"
                    else:
                        last_visit_str = f"{delta.days // 30} month{'s' if delta.days >= 60 else ''} ago"
                
                # Determine risk level (simplified - could be based on latest assessment)
                risk_level = "unknown"
                if latest_visit:
                    # Simple heuristic based on available data
                    if latest_visit.ogtt and latest_visit.ogtt > 140:
                        risk_level = "high"
                    elif latest_visit.ogtt and latest_visit.ogtt > 100:
                        risk_level = "medium"
                    elif latest_visit.ogtt:
                        risk_level = "low"
                
                patient_responses.append(PatientResponse(
                    id=patient.patient_identifier,
                    name=f"Patient {patient.patient_identifier}",  # Default name
                    age=latest_visit.age if latest_visit else None,
                    gestational_age=None,  # Not tracked currently
                    last_visit=last_visit_str,
                    risk_level=risk_level
                ))
            
            return patient_responses
            
        except Exception as e:
            logger.error(f"Error fetching patients: {str(e)}", exc_info=True)
            return []
    
    async def parse_clinical_notes(self, notes: str, patient_id: str = None) -> NotesParseResponse:
        """
        Parse clinical notes using AI to extract structured data.
        
        Args:
            notes: Clinical notes text
            patient_id: Optional patient ID for context
            
        Returns:
            NotesParseResponse with extracted and missing fields
        """
        try:
            llm = get_llm(temperature=0)
            
            prompt = self._build_extraction_prompt(notes, patient_id)
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            
            # Parse JSON response
            extracted_data = json.loads(response.content)
            
            extracted_fields = [
                ExtractedField(**field) for field in extracted_data.get("extracted", [])
            ]
            
            missing_fields = [
                MissingField(**field) for field in extracted_data.get("missing", [])
            ]
            
            return NotesParseResponse(
                extracted_fields=extracted_fields,
                missing_fields=missing_fields,
                success=True,
                message="Notes parsed successfully"
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            return NotesParseResponse(
                extracted_fields=[],
                missing_fields=[],
                success=False,
                message="Failed to parse AI response"
            )
        except Exception as e:
            logger.error(f"Error parsing notes: {str(e)}", exc_info=True)
            return NotesParseResponse(
                extracted_fields=[],
                missing_fields=[],
                success=False,
                message=f"Error: {str(e)}"
            )
    
    def create_visit(self, request: CreateVisitRequest) -> VisitResponse:
        """
        Create a new visit record for a patient.
        
        Args:
            request: CreateVisitRequest with visit data
            
        Returns:
            VisitResponse with creation status
        """
        try:
            # Verify patient exists
            patient = self.patient_repo.get_by_identifier(request.patient_id)
            if not patient:
                return VisitResponse(
                    visit_id=0,
                    patient_id=request.patient_id,
                    visit_date=datetime.utcnow(),
                    success=False,
                    message=f"Patient {request.patient_id} not found"
                )
            
            # Update patient static fields if provided
            if any([request.family_history, request.pcos, request.unexplained_prenatal_loss,
                    request.large_child_or_birth_default, request.prediabetes]):
                if request.family_history is not None:
                    patient.family_history = request.family_history
                if request.pcos is not None:
                    patient.pcos = request.pcos
                if request.unexplained_prenatal_loss is not None:
                    patient.unexplained_prenatal_loss = request.unexplained_prenatal_loss
                if request.large_child_or_birth_default is not None:
                    patient.large_child_or_birth_default = request.large_child_or_birth_default
                if request.prediabetes is not None:
                    patient.prediabetes = request.prediabetes
                
                self.patient_repo.update(patient)
            
            # Create visit record
            visit_data = {
                "patient_id": patient.id,
                "visit_date": datetime.utcnow(),
                "visit_type": request.visit_type,
                "notes": request.notes,
                "age": request.age,
                "bmi": request.bmi,
                "sys_bp": request.sys_bp,
                "dia_bp": request.dia_bp,
                "hdl": request.hdl,
                "hemoglobin": request.hemoglobin,
                "ogtt": request.ogtt,
                "no_of_pregnancy": request.no_of_pregnancy,
                "gestation_in_previous_pregnancy": request.gestation_in_previous_pregnancy,
                "sedentary_lifestyle": request.sedentary_lifestyle,
            }
            
            visit = self.visit_repo.create(visit_data)
            
            return VisitResponse(
                visit_id=visit.id,
                patient_id=request.patient_id,
                visit_date=visit.visit_date,
                success=True,
                message="Visit created successfully"
            )
            
        except Exception as e:
            logger.error(f"Error creating visit: {str(e)}", exc_info=True)
            return VisitResponse(
                visit_id=0,
                patient_id=request.patient_id,
                visit_date=datetime.utcnow(),
                success=False,
                message=f"Error creating visit: {str(e)}"
            )
    
    def _build_extraction_prompt(self, notes: str, patient_id: str = None) -> str:
        """Build prompt for clinical notes extraction."""
        return f"""Extract structured data from the following clinical notes for gestational diabetes assessment.

Clinical Notes:
{notes}

Extract the following fields if present in the notes. Return JSON format with two arrays: "extracted" and "missing".

Required fields to extract:
- Age (years)
- BMI (Body Mass Index)
- Systolic BP (mmHg)
- Diastolic BP (mmHg)
- HDL (mg/dL)
- Hemoglobin (g/dL)
- OGTT (Oral Glucose Tolerance Test, mg/dL)
- Number of Pregnancies
- Gestation in Previous Pregnancy (weeks)
- Sedentary Lifestyle (yes/no)
- Family History of Diabetes (yes/no)
- PCOS (yes/no)
- Prediabetes (yes/no)
- Unexplained Prenatal Loss (yes/no)
- Large Child or Birth Defect (yes/no)

Response format:
{{
  "extracted": [
    {{"name": "BMI", "value": 27.3, "confidence": "high", "db_field": "bmi"}},
    {{"name": "Blood Pressure", "value": "130/85", "confidence": "medium", "db_field": "sys_bp,dia_bp"}}
  ],
  "missing": [
    {{"name": "Hemoglobin", "category": "Lab Results", "db_field": "hemoglobin"}}
  ]
}}

Confidence levels:
- high: Explicitly stated in notes
- medium: Inferred or partially stated
- low: Uncertain or ambiguous

Return ONLY the JSON object, no additional text."""

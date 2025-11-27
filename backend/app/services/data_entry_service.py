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
            
            # Log the raw response for debugging
            logger.info(f"LLM raw response: {response.content[:500]}...")  # First 500 chars
            
            # Try to extract JSON from the response
            content = response.content.strip()
            
            # If response is empty
            if not content:
                logger.error("LLM returned empty response")
                return NotesParseResponse(
                    extracted_fields=[],
                    missing_fields=[],
                    success=False,
                    message="AI returned empty response"
                )
            
            # Remove markdown code blocks if present
            import re
            content = re.sub(r'^```json?\s*', '', content)  # Remove opening ```json or ```
            content = re.sub(r'\s*```$', '', content)  # Remove closing ```
            content = content.strip()
            
            # Try to find JSON in the response (in case LLM added explanatory text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content
            
            # Parse JSON response
            extracted_data = json.loads(json_str)
            
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
            logger.error(f"LLM response was: {response.content if 'response' in locals() else 'No response'}")
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
            logger.info(f"Creating visit for patient: {request.patient_id}")
            logger.info(f"Request data: notes={bool(request.notes)}, age={request.age}, bmi={request.bmi}")
            
            # Verify patient exists
            patient = self.patient_repo.get_by_identifier(request.patient_id)
            if not patient:
                error_msg = f"Patient {request.patient_id} not found"
                logger.error(error_msg)
                return VisitResponse(
                    visit_id=0,
                    patient_id=request.patient_id,
                    visit_date=datetime.utcnow(),
                    success=False,
                    message=error_msg
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
            
            # Update patient profile with clinical notes if provided
            if request.notes:
                from app.models import PatientProfile
                profile = self.session.query(PatientProfile).filter(
                    PatientProfile.patient_identifier == request.patient_id
                ).first()
                
                if profile:
                    # Append new notes to existing doctor_notes or create new
                    if profile.doctor_notes:
                        profile.doctor_notes = f"{profile.doctor_notes}\n\n[Visit {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}]\n{request.notes}"
                    else:
                        profile.doctor_notes = f"[Visit {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}]\n{request.notes}"
                    
                    profile.updated_at = datetime.utcnow()
                    self.session.add(profile)
                    # Note: Don't commit here - let visit creation handle the commit
                    logger.info(f"Prepared doctor_notes update for patient profile {request.patient_id}")
            
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

IMPORTANT: Use these EXACT database field names in db_field:
- age: Patient age in years
- bmi: Body Mass Index (number)
- sys_bp: Systolic Blood Pressure in mmHg (number)
- dia_bp: Diastolic Blood Pressure in mmHg (number)
- hdl: HDL cholesterol in mg/dL (number)
- hemoglobin: Hemoglobin level in g/dL (number)
- ogtt: Oral Glucose Tolerance Test in mg/dL (number)
- no_of_pregnancy: Number of pregnancies (integer)
- gestation_in_previous_pregnancy: Gestation weeks in previous pregnancy (integer)
- sedentary_lifestyle: Sedentary lifestyle (boolean: true/false)
- family_history: Family history of diabetes (boolean: true/false)
- pcos: PCOS diagnosis (boolean: true/false)
- prediabetes: Prediabetes condition (boolean: true/false)
- unexplained_prenatal_loss: History of unexplained prenatal loss (boolean: true/false)
- large_child_or_birth_default: Large child or birth complications (boolean: true/false)

Response format:
{{
  "extracted": [
    {{"name": "Age", "value": 28, "confidence": "high", "db_field": "age"}},
    {{"name": "BMI", "value": 27.3, "confidence": "high", "db_field": "bmi"}},
    {{"name": "Systolic BP", "value": 130, "confidence": "medium", "db_field": "sys_bp"}},
    {{"name": "Diastolic BP", "value": 85, "confidence": "medium", "db_field": "dia_bp"}},
    {{"name": "Family History", "value": true, "confidence": "high", "db_field": "family_history"}}
  ],
  "missing": [
    {{"name": "Hemoglobin", "category": "Lab Results", "db_field": "hemoglobin"}}
  ]
}}

IMPORTANT NOTES:
- For blood pressure "130/85", create TWO separate entries: one for sys_bp (130) and one for dia_bp (85)
- For boolean fields (lifestyle, conditions), return true or false, not "yes" or "no"
- Return numbers without units
- Confidence levels: high (explicitly stated), medium (inferred), low (ambiguous)

Return ONLY the JSON object, no additional text."""

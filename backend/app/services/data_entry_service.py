"""Data entry service - Handles clinical notes parsing and visit creation."""

from typing import List, Dict, Optional
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
import asyncio
from app.models import Patient
from app.models.auth import AuthUser

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
    
    def get_all_patients(self, user: Optional[AuthUser] = None) -> List[PatientResponse]:
        """
        Get all patients with their latest visit info.
        
        Returns:
            List of PatientResponse objects
        """
        try:
            if user and user.role == "patient" and user.patient_id:
                own_patient = self.session.get(Patient, user.patient_id)
                patients = [own_patient] if own_patient else []
            elif user and user.role == "doctor":
                patients = self.session.query(Patient).filter(Patient.doctor_id == user.id).all()
            else:
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
                
                # Use risk level from patient model instead of calculating from Visit
                # (risk_level is now stored directly on Patient)
                
                patient_responses.append(PatientResponse(
                    id=patient.patient_identifier,
                    name=patient.name if patient.name else f"Patient {patient.patient_identifier}",
                    age=patient.age if patient.age else None,
                    gestational_age=None,  # Not tracked currently
                    last_visit=last_visit_str,
                    risk_level=patient.risk_level if patient.risk_level else "unknown"
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
            llm = get_llm(temperature=0, max_tokens=2048)  # Increased from 512 to handle full response
            
            prompt = self._build_extraction_prompt(notes, patient_id)
            response = await asyncio.wait_for(
                llm.ainvoke([HumanMessage(content=prompt)]),
                timeout=25,
            )
            
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
        except asyncio.TimeoutError:
            logger.error("Clinical notes parsing timed out")
            return NotesParseResponse(
                extracted_fields=[],
                missing_fields=[],
                success=False,
                message="Parsing timed out. Please try shorter notes or retry."
            )
        except Exception as e:
            logger.error(f"Error parsing notes: {str(e)}", exc_info=True)
            return NotesParseResponse(
                extracted_fields=[],
                missing_fields=[],
                success=False,
                message=f"Error: {str(e)}"
            )
    
    def create_visit(self, request: CreateVisitRequest, user: Optional[AuthUser] = None) -> VisitResponse:
        """
        Create a new visit record for a patient.
        
        Args:
            request: CreateVisitRequest with visit data
            
        Returns:
            VisitResponse with creation status
        """
        try:
            logger.info(f"Creating visit for patient: {request.patient_id}")
            logger.info(f"Request data: notes={bool(request.notes)}, bmi={request.bmi}")
            
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

            # Patients can only submit visits to their own patient profile.
            if user and user.role == "patient":
                if not user.patient_id or patient.id != user.patient_id:
                    return VisitResponse(
                        visit_id=0,
                        patient_id=request.patient_id,
                        visit_date=datetime.utcnow(),
                        success=False,
                        message="Patients can only submit their own clinical notes."
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
            
            # Create Visit record (basic info only)
            from app.models import Visit
            visit = Visit(
                patient_id=patient.id,
                visit_date=datetime.utcnow(),
                visit_type=request.visit_type,
                notes=request.notes
            )
            self.session.add(visit)
            self.session.flush()  # Get visit.id without committing
            
            logger.info(f"Created visit {visit.id} for patient {patient.id}")
            
            # Create GDMAssessment if GDM data present
            if any([request.glucose_level, request.bmi, request.sys_bp, request.dia_bp,
                    request.hdl, request.ogtt, request.gestation_weeks, request.sedentary_lifestyle]):
                from app.models.assessments import GDMAssessment
                gdm = GDMAssessment(
                    visit_id=visit.id,
                    glucose_level=request.glucose_level,
                    blood_pressure_systolic=request.sys_bp,
                    blood_pressure_diastolic=request.dia_bp,
                    bmi=request.bmi,
                    hdl=request.hdl,
                    ogtt=request.ogtt,
                    gestation_weeks=request.gestation_weeks,
                    sedentary_lifestyle=request.sedentary_lifestyle
                )
                self.session.add(gdm)
                logger.info(f"Created GDMAssessment for visit {visit.id}")
            
            # Create AnemiaAssessment if CBC data present
            if any([request.wbc, request.rbc, request.hgb, request.hct,
                    request.mcv, request.mch, request.mchc, request.plt]):
                from app.models.assessments import AnemiaAssessment
                anemia = AnemiaAssessment(
                    visit_id=visit.id,
                    wbc=request.wbc,
                    rbc=request.rbc,
                    hgb=request.hgb,
                    hct=request.hct,
                    mcv=request.mcv,
                    mch=request.mch,
                    mchc=request.mchc,
                    plt=request.plt
                )
                self.session.add(anemia)
                logger.info(f"Created AnemiaAssessment for visit {visit.id}")
            
            # Create FetalHealthAssessment if CTG data present
            if any([request.baseline_value, request.accelerations, request.fetal_movement]):
                from app.models.assessments import FetalHealthAssessment
                fhp = FetalHealthAssessment(
                    visit_id=visit.id,
                    baseline_value=request.baseline_value,
                    accelerations=request.accelerations,
                    fetal_movement=request.fetal_movement
                )
                self.session.add(fhp)
                logger.info(f"Created FetalHealthAssessment for visit {visit.id}")
            
            # Commit all changes
            self.session.commit()

            
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
        return f"""Extract structured data from the following clinical notes for maternal and fetal health assessment.

Clinical Notes:
{notes}

Extract the following fields if present in the notes. Return JSON format with two arrays: "extracted" and "missing".

IMPORTANT: Use these EXACT database field names in db_field:

GDM ASSESSMENT:
- glucose_level: Blood glucose level in mg/dL (number)
- gestation_weeks: Current gestation weeks (integer)
- bmi: Body Mass Index (number)
- sys_bp: Systolic Blood Pressure in mmHg (number)
- dia_bp: Diastolic Blood Pressure in mmHg (number)
- hdl: HDL cholesterol in mg/dL (number)
- ogtt: Oral Glucose Tolerance Test in mg/dL (number)
- sedentary_lifestyle: Sedentary lifestyle (boolean: true/false)
- family_history: Family history of diabetes (boolean: true/false)
- pcos: PCOS diagnosis (boolean: true/false)
- prediabetes: Prediabetes condition (boolean: true/false)
- unexplained_prenatal_loss: History of unexplained prenatal loss (boolean: true/false)
- large_child_or_birth_default: Large child or birth complications (boolean: true/false)

ANEMIA/CBC ASSESSMENT:
- wbc: White Blood Cell count in 10⁹/L (number)
- rbc: Red Blood Cell count in 10¹²/L (number)
- hgb:  Hemoglobin in g/dL (number)
- hct: Hematocrit in % (number)
- mcv: Mean Corpuscular Volume in fL (number)
- mch: Mean Corpuscular Hemoglobin in pg (number)
- mchc: MCHC in g/dL (number)
- plt: Platelet count in 10⁹/L (number)

FETAL HEALTH/CTG ASSESSMENT:
- baseline_value: Baseline fetal heart rate in bpm (number)
- accelerations: FHR accelerations per second (number)
- fetal_movement: Fetal movements per second (number)

PREGNANCY HISTORY:
- no_of_pregnancy: Number of pregnancies (integer)
- gestation_in_previous_pregnancy: Gestation weeks in previous pregnancy (integer)

Response format:
{{
  "extracted": [
    {{"name": "Glucose Level", "value": 105, "confidence": "high", "db_field": "glucose_level"}},
    {{"name": "Gestation Weeks", "value": 28, "confidence": "high", "db_field": "gestation_weeks"}},
    {{"name": "BMI", "value": 27.3, "confidence": "high", "db_field": "bmi"}},
    {{"name": "Systolic BP", "value": 130, "confidence": "medium", "db_field": "sys_bp"}},
    {{"name": "Diastolic BP", "value": 85, "confidence": "medium", "db_field": "dia_bp"}},
    {{"name": "WBC", "value": 8.5, "confidence": "high", "db_field": "wbc"}},
    {{"name": "RBC", "value": 4.2, "confidence": "high", "db_field": "rbc"}},
    {{"name": "Hemoglobin", "value": 11.5, "confidence": "high", "db_field": "hgb"}},
    {{"name": "Baseline FHR", "value": 140, "confidence": "high", "db_field": "baseline_value"}}
  ],
  "missing": [
    {{"name": "HDL Cholesterol", "category": "Lab Results", "db_field": "hdl"}}
  ]
}}

IMPORTANT NOTES:
- For blood pressure "130/85", create TWO separate entries: one for sys_bp (130) and one for dia_bp (85)
- For boolean fields (lifestyle, conditions), return true or false, not "yes" or "no"
- Return numbers without units
- Confidence levels: high (explicitly stated), medium (inferred), low (ambiguous)
- For CBC, extract all 8 parameters if complete blood count is mentioned
- For CTG/fetal monitoring, look for baseline heart rate, accelerations, and fetal movement
- Gestation weeks is different from gestation_in_previous_pregnancy

Return ONLY the JSON object, no additional text."""

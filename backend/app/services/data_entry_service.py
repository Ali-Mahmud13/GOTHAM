"""Data entry service - Handles clinical notes parsing and visit creation."""

from typing import List, Dict, Optional
from sqlmodel import Session, select
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
from app.core import config
from app.core.llm import get_llm
from app.core.sanitize import sanitize_note
from langchain_core.messages import HumanMessage
import logging
import json
import asyncio
from app.models import Patient, Visit, UltrasoundImage
from app.models.auth import AuthUser
from app.utils.cloudinary_storage import upload_ultrasound_image, delete_ultrasound_image, is_cloudinary_configured

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
            llm = get_llm(
                temperature=0,
                max_tokens=768,
                model=config.EXTRACTION_MODEL,
            )
            
            from app.core.sanitize import safe_for_prompt
            prompt = self._build_extraction_prompt(safe_for_prompt(notes), patient_id)
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

            # Defensive filtering: sometimes the model invents fields (e.g. weight/height)
            # or returns an overly long missing list. Only keep known db_fields so we
            # never pass unexpected keys into CreateVisitRequest later.
            allowed_db_fields = {
                # GDM
                "glucose_level",
                "gestation_weeks",
                "bmi",
                "sys_bp",
                "dia_bp",
                "hdl",
                "ogtt",
                "insulin_level",
                "sedentary_lifestyle",
                "family_history",
                "pcos",
                "prediabetes",
                "unexplained_prenatal_loss",
                "large_child_or_birth_default",
                # Preeclampsia / Maternal Health
                "body_temp",
                "heart_rate",
                # CBC / Anemia
                "wbc",
                "rbc",
                "hgb",
                "hct",
                "mcv",
                "mch",
                "mchc",
                "plt",
                # Pregnancy history
                "no_of_pregnancy",
                "gestation_in_previous_pregnancy",
            }

            raw_extracted = extracted_data.get("extracted", []) or []
            raw_missing = extracted_data.get("missing", []) or []

            extracted_fields = [
                ExtractedField(**field)
                for field in raw_extracted
                if isinstance(field, dict)
                and (field.get("db_field") or field.get("dbField")) in allowed_db_fields
            ]

            missing_fields = [
                MissingField(**field)
                for field in raw_missing
                if isinstance(field, dict) and field.get("db_field") in allowed_db_fields
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

                # Registered patients cannot self-enter notes/vitals.
                if patient.doctor_id:
                    return VisitResponse(
                        visit_id=0,
                        patient_id=request.patient_id,
                        visit_date=datetime.utcnow(),
                        success=False,
                        message="You are registered with a doctor. Your doctor should enter notes and vitals."
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
                notes=sanitize_note(request.notes or "") if request.notes else None,
                recorded_by_role=user.role if user else None,
                recorded_by_user_id=user.id if user else None,
            )
            self.session.add(visit)
            self.session.flush()  # Get visit.id without committing
            
            logger.info(f"Created visit {visit.id} for patient {patient.id}")
            
            # Create GDMAssessment if GDM data present
            if any([request.glucose_level, request.bmi, request.sys_bp, request.dia_bp,
                    request.hdl, request.ogtt, request.gestation_weeks, request.sedentary_lifestyle,
                    request.insulin_level]):
                from app.models.assessments import GDMAssessment
                gdm = GDMAssessment(
                    visit_id=visit.id,
                    glucose_level=request.glucose_level,
                    blood_pressure_systolic=request.sys_bp,
                    blood_pressure_diastolic=request.dia_bp,
                    bmi=request.bmi,
                    hdl=request.hdl,
                    ogtt=request.ogtt,
                    insulin_level=request.insulin_level,
                    gestation_weeks=request.gestation_weeks,
                    sedentary_lifestyle=request.sedentary_lifestyle,
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
            
            # Create FetalHealthAssessment if any CTG data present
            if any([request.baseline_value, request.accelerations, request.fetal_movement,
                    request.uterine_contractions, request.light_decelerations,
                    request.severe_decelerations, request.prolongued_decelerations,
                    request.abnormal_short_term_variability,
                    request.mean_value_of_short_term_variability,
                    request.percentage_of_time_with_abnormal_long_term_variability,
                    request.mean_value_of_long_term_variability,
                    request.histogram_width, request.histogram_min, request.histogram_max,
                    request.histogram_number_of_peaks, request.histogram_number_of_zeroes,
                    request.histogram_mode, request.histogram_mean, request.histogram_median,
                    request.histogram_variance, request.histogram_tendency]):
                from app.models.assessments import FetalHealthAssessment
                fhp = FetalHealthAssessment(
                    visit_id=visit.id,
                    baseline_value=request.baseline_value,
                    accelerations=request.accelerations,
                    fetal_movement=request.fetal_movement,
                    uterine_contractions=request.uterine_contractions,
                    light_decelerations=request.light_decelerations,
                    severe_decelerations=request.severe_decelerations,
                    prolongued_decelerations=request.prolongued_decelerations,
                    abnormal_short_term_variability=request.abnormal_short_term_variability,
                    mean_value_of_short_term_variability=request.mean_value_of_short_term_variability,
                    percentage_of_time_with_abnormal_long_term_variability=request.percentage_of_time_with_abnormal_long_term_variability,
                    mean_value_of_long_term_variability=request.mean_value_of_long_term_variability,
                    histogram_width=request.histogram_width,
                    histogram_min=request.histogram_min,
                    histogram_max=request.histogram_max,
                    histogram_number_of_peaks=request.histogram_number_of_peaks,
                    histogram_number_of_zeroes=request.histogram_number_of_zeroes,
                    histogram_mode=request.histogram_mode,
                    histogram_mean=request.histogram_mean,
                    histogram_median=request.histogram_median,
                    histogram_variance=request.histogram_variance,
                    histogram_tendency=request.histogram_tendency,
                )
                self.session.add(fhp)
                logger.info(f"Created FetalHealthAssessment for visit {visit.id}")

            # Create MaternalHealthAssessment if preeclampsia inputs present
            if any([request.body_temp, request.heart_rate]):
                from app.models.assessments import MaternalHealthAssessment
                mha = MaternalHealthAssessment(
                    visit_id=visit.id,
                    body_temp=request.body_temp,
                    heart_rate=request.heart_rate,
                )
                self.session.add(mha)
                logger.info(f"Created MaternalHealthAssessment for visit {visit.id}")
            
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

    def upload_ultrasound_images(
        self,
        visit_id: int,
        files: List,
        user: Optional[AuthUser] = None,
    ) -> List[UltrasoundImage]:
        """Upload one or more ultrasound images to Cloudinary and store metadata."""
        if not files:
            return []

        if not is_cloudinary_configured():
            raise ValueError("Cloudinary credentials are missing. Configure CLOUDINARY_* env vars.")

        visit = self.session.get(Visit, visit_id)
        if not visit:
            raise ValueError("Visit not found")

        patient = self.session.get(Patient, visit.patient_id)
        if not patient:
            raise ValueError("Patient not found for visit")

        self._validate_upload_access(patient, user)

        allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
        max_bytes = 10 * 1024 * 1024

        uploaded_records: List[UltrasoundImage] = []
        for file in files:
            if not file or not getattr(file, "filename", None):
                continue

            content_type = (getattr(file, "content_type", "") or "").lower()
            if content_type not in allowed_types:
                raise ValueError(f"Unsupported file type: {content_type or 'unknown'}")

            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            if file_size > max_bytes:
                raise ValueError(f"File {file.filename} exceeds 10MB limit")

            cloudinary_meta = upload_ultrasound_image(
                file_obj=file.file,
                patient_identifier=patient.patient_identifier,
                visit_id=visit.id,
                filename=file.filename,
            )

            image_record = UltrasoundImage(
                visit_id=visit.id,
                patient_id=patient.id,
                public_id=cloudinary_meta["public_id"],
                secure_url=cloudinary_meta["secure_url"],
                thumbnail_url=cloudinary_meta.get("thumbnail_url"),
                file_name=cloudinary_meta.get("file_name"),
                format=cloudinary_meta.get("format"),
                bytes=cloudinary_meta.get("bytes") or file_size,
                width=cloudinary_meta.get("width"),
                height=cloudinary_meta.get("height"),
                uploaded_by_role=user.role if user else None,
                uploaded_by_user_id=user.id if user else None,
            )
            self.session.add(image_record)
            uploaded_records.append(image_record)

        self.session.commit()

        for record in uploaded_records:
            self.session.refresh(record)

        return uploaded_records

    def delete_ultrasound_image(self, image_id: int, user: Optional[AuthUser] = None) -> None:
        """Delete a stored ultrasound image from DB and Cloudinary."""
        image = self.session.get(UltrasoundImage, image_id)
        if not image:
            raise ValueError("Ultrasound image not found")

        patient = self.session.get(Patient, image.patient_id)
        if not patient:
            raise ValueError("Patient not found for ultrasound image")

        self._validate_delete_access(patient, user)

        if image.public_id:
            delete_ultrasound_image(image.public_id)

        self.session.delete(image)
        self.session.commit()

    def _validate_upload_access(self, patient: Patient, user: Optional[AuthUser]) -> None:
        """Authorize upload operations for patient or doctor context."""
        if not user:
            return

        if user.role == "patient":
            if not user.patient_id or user.patient_id != patient.id:
                raise ValueError("Patients can only modify their own data")
            if patient.doctor_id:
                raise ValueError("You are registered with a doctor. Your doctor should enter notes and vitals.")
            return

        if user.role == "doctor":
            if patient.doctor_id != user.id:
                raise ValueError("You can only modify records for your registered patients")
            return

    def _validate_delete_access(self, patient: Patient, user: Optional[AuthUser]) -> None:
        """Authorize delete operations for patient or doctor context."""
        if not user:
            return

        if user.role == "patient":
            if not user.patient_id or user.patient_id != patient.id:
                raise ValueError("Patients can only delete their own ultrasound images")
            return

        if user.role == "doctor":
            if patient.doctor_id != user.id:
                raise ValueError("You can only delete records for your registered patients")
            return
    
    def _build_extraction_prompt(self, notes: str, patient_id: str = None) -> str:
        """Build prompt for clinical notes extraction."""
        return f"""Extract structured data from the following clinical notes for maternal and fetal health assessment.

Clinical Notes:
{notes}

Extract the following fields if present in the notes. Return JSON format with two arrays: "extracted" and "missing".

CRITICAL: Keep the output SHORT and VALID JSON.
- Only include fields that appear in the notes.
- For \"missing\", include AT MOST 15 items (prioritize core vitals/labs: glucose_level, gestation_weeks, bmi, sys_bp, dia_bp, hgb, wbc, rbc, body_temp, heart_rate).
- Do NOT include any fields outside the allowed db_field list below.

IMPORTANT: Use these EXACT database field names in db_field:

GDM ASSESSMENT:
- glucose_level: Blood glucose level in mg/dL (number)
- gestation_weeks: Current gestation weeks (integer)
- bmi: Body Mass Index (number)
- sys_bp: Systolic Blood Pressure in mmHg (number)
- dia_bp: Diastolic Blood Pressure in mmHg (number)
- hdl: HDL cholesterol in mg/dL (number)
- ogtt: Oral Glucose Tolerance Test in mg/dL (number)
- insulin_level: Insulin level in μU/mL (number)
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

PREECLAMPSIA / MATERNAL HEALTH ASSESSMENT:
- body_temp: Body temperature in °C (number, e.g. 37.2)
- heart_rate: Heart rate in bpm (integer, e.g. 88)

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
    {{"name": "Hemoglobin", "value": 11.5, "confidence": "high", "db_field": "hgb"}}
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
- Gestation weeks is different from gestation_in_previous_pregnancy

Return ONLY the JSON object, no additional text."""

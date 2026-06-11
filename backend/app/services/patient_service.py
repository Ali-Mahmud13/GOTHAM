"""Patient service - Handles patient data fetching and management."""

from typing import Dict, Optional, List
import difflib
import re
from sqlmodel import Session, select
from sqlalchemy import func
from app.db.session import engine
from app.models import Patient, Visit, GDMAssessment, AnemiaAssessment, FetalHealthAssessment, MaternalHealthAssessment, UltrasoundImage
from app.models.patient_latest_assessments import PatientLatestAssessments
import logging

logger = logging.getLogger(__name__)


class PatientService:
    """Service class for managing patient data via database."""
    
    def __init__(self):
        """Initialize the patient service."""
        logger.info("Patient service initialized with database connection")

    def _normalize_patient_query(self, patient_query: str) -> str:
        """Normalize patient lookup input for robust matching."""
        normalized = (patient_query or "").strip().lower()
        normalized = normalized.strip(" .,!?:;\"'`")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _resolve_patient(self, session: Session, patient_query: str) -> Optional[Patient]:
        """Resolve patient by identifier OR name using case-insensitive matching."""
        normalized = self._normalize_patient_query(patient_query)
        if not normalized:
            return None

        statement = select(Patient).where(
            (func.lower(Patient.patient_identifier) == normalized)
            | (func.lower(Patient.name) == normalized)
        )
        patient = session.exec(statement).first()
        if patient:
            return patient

        # Fuzzy fallback for small typos in names (e.g., "Ariana Grade" vs "Ariana Grande")
        # We first narrow candidates using the first token (keeps query fast), then pick the
        # closest full-name match with a conservative similarity threshold.
        tokens = [t for t in normalized.split(" ") if t]
        if not tokens:
            return None

        first = tokens[0]
        candidates = session.exec(
            select(Patient).where(func.lower(Patient.name).like(f"%{first}%"))
        ).all()
        if not candidates:
            return None

        scored: list[tuple[float, Patient]] = []
        for c in candidates:
            name_norm = self._normalize_patient_query(c.name)
            score = difflib.SequenceMatcher(a=normalized, b=name_norm).ratio()
            scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_patient = scored[0]
        if best_score >= 0.82:
            logger.info(
                f"[FUZZY] Resolved patient '{patient_query}' → '{best_patient.name}' "
                f"(score={best_score:.2f})"
            )
            return best_patient

        return None
    
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
                # Fetch patient by identifier or name (case-insensitive)
                patient = self._resolve_patient(session, patient_identifier)
                
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
    
    async def get_patient_data_optimized(self, patient_identifier: str) -> Dict:
        """
        Optimized patient data retrieval using materialized table.
        
        Performance: 2 queries instead of 13+ (6-8x faster)
        - Query 1: Get patient
        - Query 2: Get latest assessments from materialized table
        - Query 3: Get latest visit for metadata
        
        Args:
            patient_identifier: The patient ID to search for
            
        Returns:
            Dictionary containing patient data with latest field values
        """
        try:
            logger.info(f"[OPTIMIZED] Fetching data for patient: {patient_identifier}")
            
            with Session(engine) as session:
                # Query 1: Get patient by identifier or name (case-insensitive)
                patient = self._resolve_patient(session, patient_identifier)
                
                if not patient:
                    logger.warning(f"No patient found with identifier: {patient_identifier}")
                    return {}
                
                logger.info(f"Found patient: {patient.name} (ID: {patient.id})")
                
                # Query 2: Get latest assessments from materialized table (SINGLE QUERY!)
                latest = session.get(PatientLatestAssessments, patient.id)
                
                # WORKAROUND: If CBC/CTG fields are None, fetch directly via SQL
                if latest and latest.wbc is None:
                    logger.info("[WORKAROUND] CBC fields are None, fetching via direct SQL...")
                    # Fetch directly via SQL to bypass ORM mapping issues
                    from sqlalchemy import text
                    result = session.exec(text("""
                        SELECT wbc, rbc, hgb, hct, mcv, mch, mchc, plt,
                               uterine_contractions, light_decelerations, severe_decelerations,
                               prolongued_decelerations, abnormal_short_term_variability,
                               mean_value_of_short_term_variability,
                               percentage_of_time_with_abnormal_long_term_variability,
                               mean_value_of_long_term_variability,
                               histogram_width, histogram_min, histogram_max,
                               histogram_number_of_peaks, histogram_number_of_zeroes,
                               histogram_mode, histogram_mean, histogram_median,
                               histogram_variance, histogram_tendency
                        FROM patient_latest_assessments
                        WHERE patient_id = :patient_id
                    """), {"patient_id": patient.id}).first()
                    
                    if result:
                        logger.info(f"[WORKAROUND] Fetched CBC data via SQL: WBC={result[0]}, HGB={result[2]}")
                        # Manually set attributes
                        latest.wbc, latest.rbc, latest.hgb, latest.hct = result[0], result[1], result[2], result[3]
                        latest.mcv, latest.mch, latest.mchc, latest.plt = result[4], result[5], result[6], result[7]
                        latest.uterine_contractions = result[8]
                        latest.light_decelerations = result[9]
                        latest.severe_decelerations = result[10]
                        latest.prolongued_decelerations = result[11]
                        latest.abnormal_short_term_variability = result[12]
                        latest.mean_value_of_short_term_variability = result[13]
                        latest.percentage_of_time_with_abnormal_long_term_variability = result[14]
                        latest.mean_value_of_long_term_variability = result[15]
                        latest.histogram_width = result[16]
                        latest.histogram_min = result[17]
                        latest.histogram_max = result[18]
                        latest.histogram_number_of_peaks = result[19]
                        latest.histogram_number_of_zeroes = result[20]
                        latest.histogram_mode = result[21]
                        latest.histogram_mean = result[22]
                        latest.histogram_median = result[23]
                        latest.histogram_variance = result[24]
                        latest.histogram_tendency = result[25]
                
                # Query 3: Get latest visit for metadata only
                latest_visit = session.exec(
                    select(Visit)
                    .where(Visit.patient_id == patient.id)
                    .order_by(Visit.visit_date.desc())
                ).first()

                ultrasound_refs = session.exec(
                    select(UltrasoundImage)
                    .where(UltrasoundImage.patient_id == patient.id)
                    .order_by(UltrasoundImage.created_at.desc())
                    .limit(5)
                ).all()
                
                # Query 4: Latest MaternalHealthAssessment for Preeclampsia model inputs
                mha = session.exec(
                    select(MaternalHealthAssessment)
                    .join(Visit, MaternalHealthAssessment.visit_id == Visit.id)
                    .where(Visit.patient_id == patient.id)
                    .order_by(MaternalHealthAssessment.created_at.desc())
                ).first()

                # Build response
                patient_data = self._build_patient_response_optimized(patient, latest, latest_visit, ultrasound_refs)

                # Add Preeclampsia model inputs from latest MaternalHealthAssessment
                if mha:
                    if mha.body_temp is not None:
                        patient_data["body_temp"] = mha.body_temp
                    if mha.heart_rate is not None:
                        patient_data["heart_rate"] = mha.heart_rate

                logger.info(f"[OPTIMIZED] Successfully built patient response with {len(patient_data)} fields (4 queries)")
                
                return patient_data
                
        except Exception as e:
            logger.error(f"Error fetching patient data (optimized): {str(e)}", exc_info=True)
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
                patient = self._resolve_patient(session, patient_identifier)
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
                # Get patient by identifier or name (case-insensitive)
                patient = self._resolve_patient(session, patient_identifier)
                
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
        return merged
    
    def _build_patient_response_optimized(
        self,
        patient: Patient,
        latest: Optional[PatientLatestAssessments],
        latest_visit: Optional[Visit],
        ultrasound_refs: Optional[List[UltrasoundImage]] = None,
    ) -> Dict:
        """
        Build patient response from materialized table (optimized).
        
        No visit iteration needed - single lookup in materialized table.
        
        Args:
            patient: Patient model instance
            latest: Latest assessments from materialized table
            latest_visit: Latest visit for metadata
            
        Returns:
            Dictionary with patient data and latest assessment values
        """
        response = {
            # Patient identifier
            "Patient_ID": patient.patient_identifier,
            "name": patient.name,
            "age": patient.age,
            "contact_number": patient.contact_number,
            "risk_level": patient.risk_level,
            
            # Static medical history
            "family_history": patient.family_history,
            "pcos": patient.pcos,
            "unexplained_prenatal_loss": patient.unexplained_prenatal_loss,
            "large_child_or_birth_default": patient.large_child_or_birth_default,
            "prediabetes": patient.prediabetes,
            
            # ML model field names
            "no_of_pregnancy": patient.number_of_pregnancies,
            "bmi_category": patient.bmi_category,
            
            # Smart defaults
            "gestation_in_previous_pregnancy": 0 if patient.number_of_pregnancies == 1 else 38,
            "sedentary_lifestyle": False,
            "hdl": 50.0,
            "hemoglobin": 12.0,
        }
        
        # Add visit metadata
        if latest_visit:
            response["visit_date"] = latest_visit.visit_date.isoformat()
            response["visit_type"] = latest_visit.visit_type
            response["visit_notes"] = latest_visit.notes

        if ultrasound_refs:
            latest_image = ultrasound_refs[0]
            response["latest_ultrasound_image_url"] = latest_image.secure_url
            response["latest_ultrasound_thumbnail_url"] = latest_image.thumbnail_url
            response["latest_ultrasound_visit_id"] = latest_image.visit_id
            response["ultrasound_images"] = [
                {
                    "id": image.id,
                    "visit_id": image.visit_id,
                    "public_id": image.public_id,
                    "secure_url": image.secure_url,
                    "thumbnail_url": image.thumbnail_url,
                    "uploaded_by_role": image.uploaded_by_role,
                    "created_at": image.created_at.isoformat() if image.created_at else None,
                }
                for image in ultrasound_refs
            ]
        
        # Add assessment data from materialized table
        if latest:
            # GDM fields
            if latest.glucose_level is not None:
                response["glucose_level"] = latest.glucose_level
            if latest.gestation_weeks is not None:
                response["gestation_weeks"] = latest.gestation_weeks
            if latest.sys_bp is not None:
                response["sys_bp"] = latest.sys_bp
            if latest.dia_bp is not None:
                response["dia_bp"] = latest.dia_bp
            if latest.bmi is not None:
                response["bmi"] = latest.bmi
            if latest.ogtt is not None:
                response["ogtt"] = latest.ogtt
            if latest.hdl is not None:
                response["hdl"] = latest.hdl
            if latest.sedentary_lifestyle is not None:
                response["sedentary_lifestyle"] = latest.sedentary_lifestyle
            
            # Anemia/CBC fields
            if latest.wbc is not None:
                response["WBC"] = latest.wbc
            if latest.rbc is not None:
                response["RBC"] = latest.rbc
            if latest.hgb is not None:
                response["HGB"] = latest.hgb
                response["hemoglobin"] = latest.hgb  # Backward compatibility
            if latest.hct is not None:
                response["HCT"] = latest.hct
            if latest.mcv is not None:
                response["MCV"] = latest.mcv
            if latest.mch is not None:
                response["MCH"] = latest.mch
            if latest.mchc is not None:
                response["MCHC"] = latest.mchc
            if latest.plt is not None:
                response["PLT"] = latest.plt
            
            # Fetal Health fields - ALL CTG parameters for ML model
            if latest.fetal_baseline_value is not None:
                response["baseline_value"] = latest.fetal_baseline_value
            if latest.fetal_accelerations is not None:
                response["accelerations"] = latest.fetal_accelerations
            if latest.fetal_movement is not None:
                response["fetal_movement"] = latest.fetal_movement
            if latest.uterine_contractions is not None:
                response["uterine_contractions"] = latest.uterine_contractions
            if latest.light_decelerations is not None:
                response["light_decelerations"] = latest.light_decelerations
            if latest.severe_decelerations is not None:
                response["severe_decelerations"] = latest.severe_decelerations
            if latest.prolongued_decelerations is not None:
                response["prolongued_decelerations"] = latest.prolongued_decelerations
            if latest.abnormal_short_term_variability is not None:
                response["abnormal_short_term_variability"] = latest.abnormal_short_term_variability
            if latest.mean_value_of_short_term_variability is not None:
                response["mean_value_of_short_term_variability"] = latest.mean_value_of_short_term_variability
            if latest.percentage_of_time_with_abnormal_long_term_variability is not None:
                response["percentage_of_time_with_abnormal_long_term_variability"] = latest.percentage_of_time_with_abnormal_long_term_variability
            if latest.mean_value_of_long_term_variability is not None:
                response["mean_value_of_long_term_variability"] = latest.mean_value_of_long_term_variability
            if latest.histogram_width is not None:
                response["histogram_width"] = latest.histogram_width
            if latest.histogram_min is not None:
                response["histogram_min"] = latest.histogram_min
            if latest.histogram_max is not None:
                response["histogram_max"] = latest.histogram_max
            if latest.histogram_number_of_peaks is not None:
                response["histogram_number_of_peaks"] = latest.histogram_number_of_peaks
            if latest.histogram_number_of_zeroes is not None:
                response["histogram_number_of_zeroes"] = latest.histogram_number_of_zeroes
            if latest.histogram_mode is not None:
                response["histogram_mode"] = latest.histogram_mode
            if latest.histogram_mean is not None:
                response["histogram_mean"] = latest.histogram_mean
            if latest.histogram_median is not None:
                response["histogram_median"] = latest.histogram_median
            if latest.histogram_variance is not None:
                response["histogram_variance"] = latest.histogram_variance
            if latest.histogram_tendency is not None:
                response["histogram_tendency"] = latest.histogram_tendency
        
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


def get_patient_service() -> PatientService:
    """
    Get the patient service instance.
    
    Returns:
        PatientService instance
    """
    return PatientService()

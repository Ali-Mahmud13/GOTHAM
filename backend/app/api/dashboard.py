"""Dashboard statistics API endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, func
from typing import Dict, List
from datetime import datetime, timedelta, date

from app.db.session import get_session
from app.models import (
    AnemiaAssessment,
    FetalHealthAssessment,
    GDMAssessment,
    MaternalHealthAssessment,
    Patient,
    PatientRiskHistory,
    UltrasoundImage,
    Visit,
)
from app.models.auth import AuthUser
from app.core.security import get_current_user_compat, assert_patient_access

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/risk-trends")
def get_risk_trends(
    days: int = 7,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
) -> Dict:
    """Get daily high/medium counts from historical assessment outcomes."""
    window_days = max(1, min(days, 30))
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=window_days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time())

    query = (
        select(
            PatientRiskHistory.assessed_at,
            PatientRiskHistory.patient_id,
            PatientRiskHistory.risk_level,
        )
        .join(Patient, PatientRiskHistory.patient_id == Patient.id)
        .where(PatientRiskHistory.assessed_at >= start_dt)
    )

    if user.role == "doctor":
        query = query.where(Patient.doctor_id == user.id)
    elif user.role == "patient" and user.patient_id:
        query = query.where(Patient.id == user.patient_id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported role for this resource")

    rows = session.exec(query).all()

    latest_by_patient_day: Dict[tuple[date, int], tuple[datetime, str]] = {}

    for assessed_at, patient_id, risk_level in rows:
        assessment_day = assessed_at.date()
        if assessment_day < start_date or assessment_day > today:
            continue
        key = (assessment_day, patient_id)
        current = latest_by_patient_day.get(key)
        if current is None or assessed_at > current[0]:
            latest_by_patient_day[key] = (assessed_at, risk_level)

    high_by_day: Dict[date, set[int]] = {}
    medium_by_day: Dict[date, set[int]] = {}
    for (assessment_day, patient_id), (_, risk_level) in latest_by_patient_day.items():
        if risk_level == "high":
            high_by_day.setdefault(assessment_day, set()).add(patient_id)
        elif risk_level == "medium":
            medium_by_day.setdefault(assessment_day, set()).add(patient_id)

    trend = []
    for i in range(window_days):
        current_day = start_date + timedelta(days=i)
        trend.append(
            {
                "day": current_day.strftime("%a"),
                "date": current_day.isoformat(),
                "highRisk": len(high_by_day.get(current_day, set())),
                "mediumRisk": len(medium_by_day.get(current_day, set())),
            }
        )

    return {"data": trend}


@router.get("/stats")
def get_dashboard_stats(
    response: Response,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
) -> Dict:
    """Get dashboard statistics for the authenticated user (patient or doctor)."""
    response.headers["Cache-Control"] = "private, max-age=30"

    # For patients, return only their own data
    if user.role == "patient":
        if user.patient_id:
            patient = session.exec(
                select(Patient).where(Patient.id == user.patient_id)
            ).first()
            
            if patient:
                # Get visit count
                total_visits = session.exec(
                    select(func.count(Visit.id)).where(Visit.patient_id == patient.id)
                ).one()
                
                # Get assessments this week (count unique visit runs)
                week_ago = datetime.utcnow() - timedelta(days=7)
                from sqlalchemy import union

                stmt_gdm = select(GDMAssessment.visit_id).join(Visit).where(Visit.patient_id == patient.id).where(GDMAssessment.created_at >= week_ago)
                stmt_anemia = select(AnemiaAssessment.visit_id).join(Visit).where(Visit.patient_id == patient.id).where(AnemiaAssessment.created_at >= week_ago)
                stmt_fetal = select(FetalHealthAssessment.visit_id).join(Visit).where(Visit.patient_id == patient.id).where(FetalHealthAssessment.created_at >= week_ago)
                stmt_preeclampsia = select(MaternalHealthAssessment.visit_id).join(Visit).where(Visit.patient_id == patient.id).where(MaternalHealthAssessment.created_at >= week_ago)

                unique_visits = union(stmt_gdm, stmt_anemia, stmt_fetal, stmt_preeclampsia)
                assessments_this_week = session.exec(select(func.count()).select_from(unique_visits.subquery())).one()
                
                return {
                    "user_role": "patient",
                    "patient_name": patient.name,
                    "patient_identifier": patient.patient_identifier,
                    "risk_level": patient.risk_level,
                    "total_visits": total_visits or 0,
                    "assessments_this_week": assessments_this_week or 0,
                    "clinical_notes": patient.clinical_notes,
                }
        
        # Patient has no associated patient record
        return {
            "user_role": "patient",
            "error": "No patient record found"
        }
    
    # For doctors, return statistics filtered by doctor
    if user.role == "doctor":
        # Single query to aggregate all risk levels
        risk_counts = session.exec(
            select(func.count(Patient.id), Patient.risk_level)
            .where(Patient.doctor_id == user.id)
            .group_by(Patient.risk_level)
        ).all()
        
        total_patients = 0
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        unassessed_count = 0
        
        for count, risk in risk_counts:
            total_patients += count
            if risk == "high":
                high_risk_count = count
            elif risk == "medium":
                medium_risk_count = count
            elif risk == "low":
                low_risk_count = count
            elif risk == "unassessed":
                unassessed_count = count
        
        # Get patient IDs for this doctor
        doctor_patients = session.exec(
            select(Patient.id).where(Patient.doctor_id == user.id)
        ).all()
        
        # Total visits for this doctor's patients
        if doctor_patients:
            total_visits = session.exec(
                select(func.count(Visit.id))
                .where(Visit.patient_id.in_(doctor_patients))
            ).one()
            
            # Assessments this week for this doctor's patients (count unique visit runs)
            week_ago = datetime.utcnow() - timedelta(days=7)
            from sqlalchemy import union

            stmt_gdm = select(GDMAssessment.visit_id).join(Visit).where(Visit.patient_id.in_(doctor_patients)).where(GDMAssessment.created_at >= week_ago)
            stmt_anemia = select(AnemiaAssessment.visit_id).join(Visit).where(Visit.patient_id.in_(doctor_patients)).where(AnemiaAssessment.created_at >= week_ago)
            stmt_fetal = select(FetalHealthAssessment.visit_id).join(Visit).where(Visit.patient_id.in_(doctor_patients)).where(FetalHealthAssessment.created_at >= week_ago)
            stmt_preeclampsia = select(MaternalHealthAssessment.visit_id).join(Visit).where(Visit.patient_id.in_(doctor_patients)).where(MaternalHealthAssessment.created_at >= week_ago)

            unique_visits = union(stmt_gdm, stmt_anemia, stmt_fetal, stmt_preeclampsia)
            assessments_this_week = session.exec(select(func.count()).select_from(unique_visits.subquery())).one()
        else:
            total_visits = 0
            assessments_this_week = 0
        
        # Recent high-risk patients for this doctor
        high_risk_patients = session.exec(
            select(Patient)
            .where(Patient.doctor_id == user.id)
            .where(Patient.risk_level == "high")
            .order_by(Patient.updated_at.desc())
            .limit(5)
        ).all()
        
        # Recent patients for this doctor (any risk level)
        recent_patients = session.exec(
            select(Patient)
            .where(Patient.doctor_id == user.id)
            .order_by(Patient.updated_at.desc())
            .limit(5)
        ).all()
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported role for dashboard stats")

    return {
        "user_role": "doctor",
        "doctor_name": user.full_name,
        "total_patients": total_patients or 0,
        "high_risk_count": high_risk_count or 0,
        "medium_risk_count": medium_risk_count or 0,
        "low_risk_count": low_risk_count or 0,
        "unassessed_count": unassessed_count or 0,
        "total_visits": total_visits or 0,
        "assessments_this_week": assessments_this_week or 0,
        "high_risk_patients": [
            {
                "id": p.id,
                "patient_identifier": p.patient_identifier,
                "name": p.name,
                "risk_level": p.risk_level,
                "clinical_notes": p.clinical_notes,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in high_risk_patients
        ],
        "recent_patients": [
            {
                "id": p.id,
                "patient_identifier": p.patient_identifier,
                "name": p.name,
                "risk_level": p.risk_level,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in recent_patients
        ]
    }


@router.get("/patient/{patient_identifier}/visits")
def get_patient_visits(
    patient_identifier: str,
    requester: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
) -> Dict:
    """Get visit count and recent visits for a patient with full assessment data."""

    patient = session.exec(
        select(Patient).where(Patient.patient_identifier == patient_identifier)
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    assert_patient_access(requester, patient)

    total_visits = session.exec(
        select(func.count(Visit.id)).where(Visit.patient_id == patient.id)
    ).one()
    total_clinical_visits = session.exec(
        select(func.count(Visit.id))
        .where(Visit.patient_id == patient.id)
        .where(
            or_(
                Visit.visit_type.is_(None),
                Visit.visit_type.notin_(("patient_notes", "doctor_notes")),
            )
        )
    ).one()

    visits = session.exec(
        select(Visit)
        .where(Visit.patient_id == patient.id)
        .options(
            selectinload(Visit.anemia_assessment),
            selectinload(Visit.fetal_health_assessment),
            selectinload(Visit.gdm_assessment),
            selectinload(Visit.maternal_health_assessment),
            selectinload(Visit.ultrasound_images),
        )
        .order_by(Visit.visit_date.desc())
        .limit(50)
    ).all()

    visit_data = []

    for visit in visits:
        anemia = visit.anemia_assessment
        fetal = visit.fetal_health_assessment
        gdm = visit.gdm_assessment
        mha = visit.maternal_health_assessment
        ultrasound_images = sorted(
            visit.ultrasound_images or [],
            key=lambda im: im.created_at or datetime.min,
            reverse=True,
        )

        source = "unknown"
        if visit.recorded_by_role == "patient" or visit.visit_type == "patient_notes":
            source = "patient"
        elif visit.recorded_by_role == "doctor" or visit.visit_type == "doctor_notes":
            current_doctor_id = None
            if requester.role == "doctor":
                current_doctor_id = requester.id
            elif requester.role == "patient":
                current_doctor_id = patient.doctor_id
            else:
                current_doctor_id = patient.doctor_id

            if visit.recorded_by_user_id and current_doctor_id and visit.recorded_by_user_id == current_doctor_id:
                source = "current_doctor"
            elif visit.recorded_by_user_id and current_doctor_id and visit.recorded_by_user_id != current_doctor_id:
                source = "previous_doctor"
            else:
                source = "doctor"

        is_past_history = source in {"patient", "previous_doctor"}

        # Build visit data with all assessment parameters
        visit_dict = {
            "id": visit.id,
            "visit_date": visit.visit_date.isoformat(),
            "visit_type": visit.visit_type,
            "notes": visit.notes,
            "note_source": source,
            "is_past_history": is_past_history,
            
            # CBC Data from anemia assessment
            "wbc": anemia.wbc if anemia else None,
            "rbc": anemia.rbc if anemia else None,
            "hgb": anemia.hgb if anemia else None,
            "hct": anemia.hct if anemia else None,
            "mcv": anemia.mcv if anemia else None,
            "mch": anemia.mch if anemia else None,
            "mchc": anemia.mchc if anemia else None,
            "plt": anemia.plt if anemia else None,
            
            # Anemia predictions
            "anemia_diagnosis": anemia.diagnosis if anemia else None,
            
            # FHP Data from fetal health assessment
            "baseline_value": fetal.baseline_value if fetal else None,
            "accelerations": fetal.accelerations if fetal else None,
            "fetal_movement": fetal.fetal_movement if fetal else None,
            "uterine_contractions": fetal.uterine_contractions if fetal else None,
            "light_decelerations": fetal.light_decelerations if fetal else None,
            "severe_decelerations": fetal.severe_decelerations if fetal else None,
            "prolongued_decelerations": fetal.prolongued_decelerations if fetal else None,
            "abnormal_short_term_variability": fetal.abnormal_short_term_variability if fetal else None,
            "mean_value_of_short_term_variability": fetal.mean_value_of_short_term_variability if fetal else None,
            "percentage_of_time_with_abnormal_long_term_variability": (
                fetal.percentage_of_time_with_abnormal_long_term_variability if fetal else None
            ),
            "mean_value_of_long_term_variability": fetal.mean_value_of_long_term_variability if fetal else None,
            "histogram_width": fetal.histogram_width if fetal else None,
            "histogram_min": fetal.histogram_min if fetal else None,
            "histogram_max": fetal.histogram_max if fetal else None,
            "histogram_number_of_peaks": fetal.histogram_number_of_peaks if fetal else None,
            "histogram_number_of_zeroes": fetal.histogram_number_of_zeroes if fetal else None,
            "histogram_mode": fetal.histogram_mode if fetal else None,
            "histogram_mean": fetal.histogram_mean if fetal else None,
            "histogram_median": fetal.histogram_median if fetal else None,
            "histogram_variance": fetal.histogram_variance if fetal else None,
            "histogram_tendency": fetal.histogram_tendency if fetal else None,
            "fetal_health_status": fetal.status if fetal else None,
            
            # Preeclampsia data
            "body_temp":          mha.body_temp    if mha else None,
            "heart_rate":         mha.heart_rate   if mha else None,
            "maternal_risk_level": mha.risk_level  if mha else None,

            # GDM Data from GDM assessment
            "glucose_level": gdm.glucose_level if gdm else None,
            "blood_pressure_systolic": gdm.blood_pressure_systolic if gdm else None,
            "blood_pressure_diastolic": gdm.blood_pressure_diastolic if gdm else None,
            "bmi": gdm.bmi if gdm else None,
            "ogtt": gdm.ogtt if gdm else None,
            "gdm_risk_level": gdm.risk_level if gdm else None,
            "assessment_results": {
                "gdm": {
                    "status": gdm.prediction_status,
                    "severity": gdm.severity,
                    "outcome": gdm.predicted_class,
                    "oldest_input_age_days": gdm.oldest_input_age_days,
                    "has_stale_inputs": bool(gdm.has_stale_inputs),
                } if gdm else None,
                "anemia": {
                    "status": anemia.prediction_status,
                    "severity": anemia.severity,
                    "outcome": anemia.predicted_class or anemia.diagnosis,
                    "oldest_input_age_days": anemia.oldest_input_age_days,
                    "has_stale_inputs": bool(anemia.has_stale_inputs),
                } if anemia else None,
                "fetal": {
                    "status": fetal.prediction_status,
                    "severity": fetal.severity,
                    "outcome": fetal.predicted_class,
                    "oldest_input_age_days": fetal.oldest_input_age_days,
                    "has_stale_inputs": bool(fetal.has_stale_inputs),
                } if fetal else None,
                "preeclampsia": {
                    "status": mha.prediction_status,
                    "severity": mha.severity,
                    "outcome": mha.predicted_class,
                    "oldest_input_age_days": mha.oldest_input_age_days,
                    "has_stale_inputs": bool(mha.has_stale_inputs),
                } if mha else None,
            },
            "ultrasound_images": [
                {
                    "id": image.id,
                    "visit_id": image.visit_id,
                    "patient_id": image.patient_id,
                    "public_id": image.public_id,
                    "secure_url": image.secure_url,
                    "thumbnail_url": image.thumbnail_url,
                    "file_name": image.file_name,
                    "format": image.format,
                    "bytes": image.bytes,
                    "width": image.width,
                    "height": image.height,
                    "uploaded_by_role": image.uploaded_by_role,
                    "uploaded_by_user_id": image.uploaded_by_user_id,
                    "created_at": image.created_at.isoformat() if image.created_at else None,
                }
                for image in ultrasound_images
            ],
        }
        
        visit_data.append(visit_dict)
    
    return {
        "total_visits": total_visits or 0,
        "total_clinical_visits": total_clinical_visits or 0,
        "recent_visits": visit_data
    }


@router.get("/assessments/week")
def get_weekly_assessments(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
) -> List[Dict]:
    """Return this week's assessment runs for doctor's patients, grouped by visit."""
    if user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctors only.")

    week_ago = datetime.utcnow() - timedelta(days=7)

    doctor_patients = session.exec(
        select(Patient).where(Patient.doctor_id == user.id)
    ).all()
    if not doctor_patients:
        return []

    patient_ids = [p.id for p in doctor_patients]
    patient_map = {p.id: p for p in doctor_patients}

    gdm_vids = set(session.exec(
        select(GDMAssessment.visit_id).join(Visit)
        .where(Visit.patient_id.in_(patient_ids))
        .where(GDMAssessment.created_at >= week_ago)
    ).all())
    anemia_vids = set(session.exec(
        select(AnemiaAssessment.visit_id).join(Visit)
        .where(Visit.patient_id.in_(patient_ids))
        .where(AnemiaAssessment.created_at >= week_ago)
    ).all())
    fetal_vids = set(session.exec(
        select(FetalHealthAssessment.visit_id).join(Visit)
        .where(Visit.patient_id.in_(patient_ids))
        .where(FetalHealthAssessment.created_at >= week_ago)
    ).all())
    preeclampsia_vids = set(session.exec(
        select(MaternalHealthAssessment.visit_id).join(Visit)
        .where(Visit.patient_id.in_(patient_ids))
        .where(MaternalHealthAssessment.created_at >= week_ago)
    ).all())

    all_visit_ids = gdm_vids | anemia_vids | fetal_vids | preeclampsia_vids
    results = []

    for vid in all_visit_ids:
        visit = session.get(Visit, vid)
        if not visit:
            continue
        patient = patient_map.get(visit.patient_id)
        if not patient:
            continue

        gdm = session.exec(
            select(GDMAssessment)
            .where(GDMAssessment.visit_id == vid)
            .where(GDMAssessment.created_at >= week_ago)
            .order_by(GDMAssessment.created_at.desc())
        ).first()
        anemia = session.exec(
            select(AnemiaAssessment)
            .where(AnemiaAssessment.visit_id == vid)
            .where(AnemiaAssessment.created_at >= week_ago)
            .order_by(AnemiaAssessment.created_at.desc())
        ).first()
        fetal = session.exec(
            select(FetalHealthAssessment)
            .where(FetalHealthAssessment.visit_id == vid)
            .where(FetalHealthAssessment.created_at >= week_ago)
            .order_by(FetalHealthAssessment.created_at.desc())
        ).first()
        preeclampsia = session.exec(
            select(MaternalHealthAssessment)
            .where(MaternalHealthAssessment.visit_id == vid)
            .where(MaternalHealthAssessment.created_at >= week_ago)
            .order_by(MaternalHealthAssessment.created_at.desc())
        ).first()

        has_maternal = gdm or anemia or preeclampsia
        if has_maternal and fetal:
            assessment_type = "Complete"
        elif has_maternal:
            assessment_type = "Maternal"
        else:
            assessment_type = "Fetal"

        timestamps = [x.created_at for x in [gdm, anemia, fetal, preeclampsia] if x]
        run_at = max(timestamps).isoformat() if timestamps else str(visit.visit_date)

        results.append({
            "visit_id": vid,
            "patient_name": patient.name,
            "patient_identifier": patient.patient_identifier,
            "run_at": run_at,
            "assessment_type": assessment_type,
            "gdm": {"risk_level": gdm.risk_level, "confidence": gdm.confidence, "ai_report": gdm.ai_report} if gdm else None,
            "anemia": {"diagnosis": anemia.diagnosis, "confidence": anemia.confidence, "ai_report": anemia.ai_report} if anemia else None,
            "fetal": {"status": fetal.status, "confidence": fetal.confidence, "ai_report": fetal.ai_report} if fetal else None,
            "preeclampsia": {
                "risk_level": preeclampsia.risk_level,
                "confidence": preeclampsia.confidence,
                "ai_report": preeclampsia.ai_report,
            } if preeclampsia else None,
        })

    results.sort(key=lambda x: x["run_at"], reverse=True)
    return results

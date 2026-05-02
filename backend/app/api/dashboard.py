"""Dashboard statistics API endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, func
from typing import Dict
from datetime import datetime, timedelta, date

from app.db.session import get_session
from app.models import Patient, Visit, GDMAssessment, AnemiaAssessment, FetalHealthAssessment, UltrasoundImage
from app.models.auth import AuthUser
from app.core.security import get_current_user_compat, assert_patient_access

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/risk-trends")
def get_risk_trends(
    days: int = 7,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
) -> Dict:
    """Get daily high/medium risk counts based on visit activity over the last N days."""
    window_days = max(1, min(days, 30))
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=window_days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time())

    query = (
        select(Visit.visit_date, Patient.id, Patient.risk_level)
        .join(Patient, Visit.patient_id == Patient.id)
        .where(Visit.visit_date >= start_dt)
    )

    if user.role == "doctor":
        query = query.where(Patient.doctor_id == user.id)
    elif user.role == "patient" and user.patient_id:
        query = query.where(Patient.id == user.patient_id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported role for this resource")

    rows = session.exec(query).all()

    high_by_day: Dict[date, set[int]] = {}
    medium_by_day: Dict[date, set[int]] = {}

    for visit_date, patient_id, risk_level in rows:
        visit_day = visit_date.date()
        if visit_day < start_date or visit_day > today:
            continue
        if risk_level == "high":
            high_by_day.setdefault(visit_day, set()).add(patient_id)
        elif risk_level == "medium":
            medium_by_day.setdefault(visit_day, set()).add(patient_id)

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
                
                # Get assessments this week
                week_ago = datetime.utcnow() - timedelta(days=7)
                gdm_this_week = session.exec(
                    select(func.count(GDMAssessment.id))
                    .join(Visit)
                    .where(Visit.patient_id == patient.id)
                    .where(GDMAssessment.created_at >= week_ago)
                ).one()
                anemia_this_week = session.exec(
                    select(func.count(AnemiaAssessment.id))
                    .join(Visit)
                    .where(Visit.patient_id == patient.id)
                    .where(AnemiaAssessment.created_at >= week_ago)
                ).one()
                fetal_this_week = session.exec(
                    select(func.count(FetalHealthAssessment.id))
                    .join(Visit)
                    .where(Visit.patient_id == patient.id)
                    .where(FetalHealthAssessment.created_at >= week_ago)
                ).one()
                assessments_this_week = gdm_this_week + anemia_this_week + fetal_this_week
                
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
        # Filter patients by this doctor's ID
        total_patients = session.exec(
            select(func.count(Patient.id)).where(Patient.doctor_id == user.id)
        ).one()
        
        # High-risk patients for this doctor
        high_risk_count = session.exec(
            select(func.count(Patient.id))
            .where(Patient.doctor_id == user.id)
            .where(Patient.risk_level == "high")
        ).one()
        
        # Medium-risk patients for this doctor
        medium_risk_count = session.exec(
            select(func.count(Patient.id))
            .where(Patient.doctor_id == user.id)
            .where(Patient.risk_level == "medium")
        ).one()
        
        # Low-risk patients for this doctor
        low_risk_count = session.exec(
            select(func.count(Patient.id))
            .where(Patient.doctor_id == user.id)
            .where(Patient.risk_level == "low")
        ).one()
        
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
            
            # Assessments this week for this doctor's patients
            week_ago = datetime.utcnow() - timedelta(days=7)
            gdm_this_week = session.exec(
                select(func.count(GDMAssessment.id))
                .join(Visit)
                .where(Visit.patient_id.in_(doctor_patients))
                .where(GDMAssessment.created_at >= week_ago)
            ).one()
            anemia_this_week = session.exec(
                select(func.count(AnemiaAssessment.id))
                .join(Visit)
                .where(Visit.patient_id.in_(doctor_patients))
                .where(AnemiaAssessment.created_at >= week_ago)
            ).one()
            fetal_this_week = session.exec(
                select(func.count(FetalHealthAssessment.id))
                .join(Visit)
                .where(Visit.patient_id.in_(doctor_patients))
                .where(FetalHealthAssessment.created_at >= week_ago)
            ).one()
            assessments_this_week = gdm_this_week + anemia_this_week + fetal_this_week
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

    visits = session.exec(
        select(Visit)
        .where(Visit.patient_id == patient.id)
        .options(
            selectinload(Visit.anemia_assessment),
            selectinload(Visit.fetal_health_assessment),
            selectinload(Visit.gdm_assessment),
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
            "fetal_health_status": fetal.status if fetal else None,
            
            # GDM Data from GDM assessment
            "glucose_level": gdm.glucose_level if gdm else None,
            "blood_pressure_systolic": gdm.blood_pressure_systolic if gdm else None,
            "blood_pressure_diastolic": gdm.blood_pressure_diastolic if gdm else None,
            "bmi": gdm.bmi if gdm else None,
            "ogtt": gdm.ogtt if gdm else None,
            "gdm_risk_level": gdm.risk_level if gdm else None,
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
        "recent_visits": visit_data
    }

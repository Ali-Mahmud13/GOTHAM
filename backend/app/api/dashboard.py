"""Dashboard statistics API endpoint."""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select, func
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.db.session import get_session
from app.models import Patient, Visit, GDMAssessment, AnemiaAssessment, FetalHealthAssessment
from app.models.auth import AuthUser

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: Session = Depends(get_session)
) -> Dict:
    """Get dashboard statistics based on user authentication."""
    
    # Get authenticated user
    user = None
    if user_email:
        user = session.exec(
            select(AuthUser).where(AuthUser.email == user_email)
        ).first()
    
    # For patients, return only their own data
    if user and user.role == "patient":
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
    
    # For doctors (and unauthenticated access), return statistics filtered by doctor
    if user and user.role == "doctor":
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
        # For unauthenticated users, return all patients (legacy behavior)
        total_patients = session.exec(select(func.count(Patient.id))).one()
        
        high_risk_count = session.exec(
            select(func.count(Patient.id)).where(Patient.risk_level == "high")
        ).one()
        
        medium_risk_count = session.exec(
            select(func.count(Patient.id)).where(Patient.risk_level == "medium")
        ).one()
        
        low_risk_count = session.exec(
            select(func.count(Patient.id)).where(Patient.risk_level == "low")
        ).one()
        
        total_visits = session.exec(select(func.count(Visit.id))).one()
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        gdm_this_week = session.exec(
            select(func.count(GDMAssessment.id)).where(GDMAssessment.created_at >= week_ago)
        ).one()
        anemia_this_week = session.exec(
            select(func.count(AnemiaAssessment.id)).where(AnemiaAssessment.created_at >= week_ago)
        ).one()
        fetal_this_week = session.exec(
            select(func.count(FetalHealthAssessment.id)).where(FetalHealthAssessment.created_at >= week_ago)
        ).one()
        assessments_this_week = gdm_this_week + anemia_this_week + fetal_this_week
        
        high_risk_patients = session.exec(
            select(Patient)
            .where(Patient.risk_level == "high")
            .order_by(Patient.updated_at.desc())
            .limit(5)
        ).all()
        
        recent_patients = session.exec(
            select(Patient)
            .order_by(Patient.updated_at.desc())
            .limit(5)
        ).all()
    
    return {
        "user_role": "doctor" if user and user.role == "doctor" else "unknown",
        "doctor_name": user.full_name if user and user.role == "doctor" else None,
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
def get_patient_visits(patient_identifier: str, session: Session = Depends(get_session)) -> Dict:
    """Get visit count and recent visits for a patient with full assessment data."""
    
    # Get patient
    patient = session.exec(
        select(Patient).where(Patient.patient_identifier == patient_identifier)
    ).first()
    
    if not patient:
        return {"total_visits": 0, "recent_visits": []}
    
    # Total visits
    total_visits = session.exec(
        select(func.count(Visit.id)).where(Visit.patient_id == patient.id)
    ).one()
    
    # Recent visits with full assessment data
    visits = session.exec(
        select(Visit)
        .where(Visit.patient_id == patient.id)
        .order_by(Visit.visit_date.desc())
        .limit(10)
    ).all()
    
    visit_data = []
    for visit in visits:
        # Get anemia assessment data
        anemia = session.exec(
            select(AnemiaAssessment).where(AnemiaAssessment.visit_id == visit.id)
        ).first()
        
        # Get fetal health assessment data
        fetal = session.exec(
            select(FetalHealthAssessment).where(FetalHealthAssessment.visit_id == visit.id)
        ).first()
        
        # Get GDM assessment data
        gdm = session.exec(
            select(GDMAssessment).where(GDMAssessment.visit_id == visit.id)
        ).first()
        
        # Build visit data with all assessment parameters
        visit_dict = {
            "id": visit.id,
            "visit_date": visit.visit_date.isoformat(),
            "visit_type": visit.visit_type,
            "notes": visit.notes,
            
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
            "anemia_confidence": anemia.confidence if anemia else None,
            
            # FHP Data from fetal health assessment
            "baseline_value": fetal.baseline_value if fetal else None,
            "accelerations": fetal.accelerations if fetal else None,
            "fetal_health_status": fetal.status if fetal else None,
            "fetal_health_confidence": fetal.confidence if fetal else None,
            
            # GDM Data from GDM assessment
            "glucose_level": gdm.glucose_level if gdm else None,
            "blood_pressure_systolic": gdm.blood_pressure_systolic if gdm else None,
            "blood_pressure_diastolic": gdm.blood_pressure_diastolic if gdm else None,
            "bmi": gdm.bmi if gdm else None,
            "ogtt": gdm.ogtt if gdm else None,
            "gdm_risk_level": gdm.risk_level if gdm else None,
            "gdm_confidence": gdm.confidence if gdm else None,
        }
        
        visit_data.append(visit_dict)
    
    return {
        "total_visits": total_visits or 0,
        "recent_visits": visit_data
    }

"""Dashboard statistics API endpoint."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from typing import Dict, List
from datetime import datetime, timedelta

from app.db.session import get_session
from app.models import Patient, Visit, GDMAssessment, AnemiaAssessment, FetalHealthAssessment

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(session: Session = Depends(get_session)) -> Dict:
    """Get dashboard statistics."""
    
    # Total active patients
    total_patients = session.exec(select(func.count(Patient.id))).one()
    
    # High-risk patients
    high_risk_count = session.exec(
        select(func.count(Patient.id)).where(Patient.risk_level == "high")
    ).one()
    
    # Medium-risk patients
    medium_risk_count = session.exec(
        select(func.count(Patient.id)).where(Patient.risk_level == "medium")
    ).one()
    
    # Low-risk patients  
    low_risk_count = session.exec(
        select(func.count(Patient.id)).where(Patient.risk_level == "low")
    ).one()
    
    # Total visits
    total_visits = session.exec(select(func.count(Visit.id))).one()
    
    # Assessments this week
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
    
    # Recent high-risk patients
    high_risk_patients = session.exec(
        select(Patient)
        .where(Patient.risk_level == "high")
        .order_by(Patient.updated_at.desc())
        .limit(5)
    ).all()
    
    # Recent patients (any risk level)
    recent_patients = session.exec(
        select(Patient)
        .order_by(Patient.updated_at.desc())
        .limit(5)
    ).all()
    
    return {
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

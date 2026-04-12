"""Persistence helpers for storing generated assessment reports in DB."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import Session, select

from app.db.session import engine
from app.models import Patient, Visit, GDMAssessment, AnemiaAssessment, FetalHealthAssessment
import re

def _compact_assessment_report(report: str) -> str:
    if not report:
        return report
    text = report
    noisy_headers = ["## Confidence Scores",
                     "## Explainable AI Analysis",
                     "## Key Clinical Insights",
                     "## Interpretation Notes",
                     "## Detected Structures",
                     "## Patient Information",]
    for h in noisy_headers:
        pattern = rf"{re.escape(h)}[\s\S]*?(?=\n## |\Z)"
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

def _to_gdm_risk_value(level: Optional[str]) -> Optional[int]:
    if not level:
        return None
    normalized = level.lower().strip()
    if normalized == "high":
        return 2
    if normalized in {"medium", "elevated"}:
        return 1
    if normalized == "low":
        return 0
    return None


def _to_fetal_status_value(level: Optional[str]) -> Optional[int]:
    if not level:
        return None
    normalized = level.lower().strip()
    if normalized == "high":
        return 3
    if normalized in {"medium", "elevated"}:
        return 2
    if normalized == "low":
        return 1
    return None


def save_assessment_report(
    patient_identifier: str,
    assessment_type: str,
    assessment_report: str,
    risk_levels: Optional[dict] = None,
) -> bool:
    """Save only structured assessment report output to latest assessment records."""
    if not patient_identifier or not assessment_report:
        return False
    assessment_report = _compact_assessment_report(assessment_report)

    risk_levels = risk_levels or {}

    with Session(engine) as session:
        patient = session.exec(
            select(Patient).where(Patient.patient_identifier == patient_identifier)
        ).first()

        if not patient:
            return False

        latest_visit = session.exec(
            select(Visit)
            .where(Visit.patient_id == patient.id)
            .order_by(Visit.visit_date.desc())
        ).first()

        if not latest_visit:
            return False

        if assessment_type in {"maternal", "both"}:
            gdm = session.exec(select(GDMAssessment).where(GDMAssessment.visit_id == latest_visit.id)).first()
            if not gdm:
                gdm = GDMAssessment(visit_id=latest_visit.id)
            gdm.ai_report = assessment_report
            gdm_risk = _to_gdm_risk_value(risk_levels.get("gdm"))
            if gdm_risk is not None:
                gdm.risk_level = gdm_risk
            session.add(gdm)

            anemia = session.exec(select(AnemiaAssessment).where(AnemiaAssessment.visit_id == latest_visit.id)).first()
            if not anemia:
                anemia = AnemiaAssessment(visit_id=latest_visit.id)
            anemia.ai_report = assessment_report
            session.add(anemia)

        if assessment_type in {"fetal", "both"}:
            fetal = session.exec(select(FetalHealthAssessment).where(FetalHealthAssessment.visit_id == latest_visit.id)).first()
            if not fetal:
                fetal = FetalHealthAssessment(visit_id=latest_visit.id)
            fetal.ai_report = assessment_report
            fetal_status = _to_fetal_status_value(risk_levels.get("fetal"))
            if fetal_status is not None:
                fetal.status = fetal_status
            session.add(fetal)

        overall_risk = None
        if assessment_type in {"maternal", "both"}:
            overall_risk = risk_levels.get("gdm") or risk_levels.get("anemia")
        if assessment_type in {"fetal", "both"}:
            fetal_risk = risk_levels.get("fetal")
            if fetal_risk == "high":
                overall_risk = "high"
            elif fetal_risk == "medium" and overall_risk != "high":
                overall_risk = "medium"
            elif not overall_risk:
                overall_risk = fetal_risk

        if overall_risk in {"low", "medium", "high"}:
            patient.risk_level = overall_risk

        patient.updated_at = datetime.utcnow()
        session.add(patient)
        session.commit()

        return True
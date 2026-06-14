"""Centralized normalization and patient-level risk aggregation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models import (
    AnemiaAssessment,
    FetalHealthAssessment,
    GDMAssessment,
    MaternalHealthAssessment,
    Patient,
    PatientRiskHistory,
    Visit,
)

RISK_ORDER = {"unassessed": -1, "low": 0, "medium": 1, "high": 2}
VALID_RISKS = frozenset(RISK_ORDER)


def normalize_risk(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized == "elevated":
        return "medium"
    if normalized == "mid":
        return "medium"
    return normalized if normalized in VALID_RISKS else None


def highest_risk(values: list[Optional[str]]) -> str:
    known = [normalize_risk(value) for value in values]
    known = [value for value in known if value and value != "unassessed"]
    if not known:
        return "unassessed"
    return max(known, key=lambda value: RISK_ORDER[value])


def anemia_severity(diagnosis: Optional[str]) -> Optional[str]:
    if not diagnosis:
        return None
    return "low" if diagnosis.strip().lower() == "healthy" else "high"


def _latest_completed_severity(
    session: Session,
    patient_id: int,
    model,
) -> Optional[str]:
    row = session.exec(
        select(model)
        .join(Visit, model.visit_id == Visit.id)
        .where(Visit.patient_id == patient_id)
        .where(model.prediction_status == "completed")
        .where(model.severity.is_not(None))
        .order_by(model.created_at.desc(), model.id.desc())
    ).first()
    return normalize_risk(row.severity) if row else None


def latest_model_severities(session: Session, patient_id: int) -> dict[str, str]:
    severities = {
        "gdm": _latest_completed_severity(session, patient_id, GDMAssessment),
        "anemia": _latest_completed_severity(session, patient_id, AnemiaAssessment),
        "preeclampsia": _latest_completed_severity(
            session, patient_id, MaternalHealthAssessment
        ),
        "fetal": _latest_completed_severity(
            session, patient_id, FetalHealthAssessment
        ),
    }
    return {key: value for key, value in severities.items() if value}


def recompute_patient_risk(
    session: Session,
    patient: Patient,
    *,
    visit_id: Optional[int] = None,
    assessment_type: Optional[str] = None,
    record_history: bool = True,
    assessed_at: Optional[datetime] = None,
) -> str:
    severities = latest_model_severities(session, patient.id)
    overall = highest_risk(list(severities.values()))
    patient.risk_level = overall
    patient.updated_at = datetime.utcnow()
    session.add(patient)

    if record_history and severities:
        session.add(
            PatientRiskHistory(
                patient_id=patient.id,
                visit_id=visit_id,
                risk_level=overall,
                assessment_type=assessment_type,
                model_severities=severities,
                assessed_at=assessed_at or datetime.utcnow(),
            )
        )

    return overall

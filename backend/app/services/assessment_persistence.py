"""Persistence helpers for storing generated assessment reports in DB."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import Session, select
from sqlalchemy import func
import difflib

from app.db.session import engine
from app.models import Patient, Visit, GDMAssessment, AnemiaAssessment, FetalHealthAssessment, MaternalHealthAssessment
from app.services.risk_service import recompute_patient_risk
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


def _normalize_patient_query(patient_query: str) -> str:
    normalized = (patient_query or "").strip().lower()
    normalized = normalized.strip(" .,!?:;\"'`")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _resolve_patient(session: Session, patient_query: str) -> Optional[Patient]:
    """
    Resolve patient by identifier OR name using case-insensitive matching,
    with a fuzzy fallback for small typos in names.
    """
    normalized = _normalize_patient_query(patient_query)
    if not normalized:
        return None

    patient = session.exec(
        select(Patient).where(
            (func.lower(Patient.patient_identifier) == normalized)
            | (func.lower(Patient.name) == normalized)
        )
    ).first()
    if patient:
        return patient

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
        name_norm = _normalize_patient_query(c.name)
        score = difflib.SequenceMatcher(a=normalized, b=name_norm).ratio()
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_patient = scored[0]
    return best_patient if best_score >= 0.82 else None


def save_assessment_report(
    patient_identifier: str,
    assessment_type: str,
    assessment_report: str,
    risk_levels: Optional[dict] = None,
    model_results: Optional[dict] = None,
) -> bool:
    """Persist completed structured model results and recompute overall risk."""
    if not patient_identifier or not assessment_report:
        return False
    assessment_report = _compact_assessment_report(assessment_report)

    model_results = model_results or {}

    with Session(engine) as session:
        patient = _resolve_patient(session, patient_identifier)

        if not patient:
            return False

        latest_visit = session.exec(
            select(Visit)
            .where(Visit.patient_id == patient.id)
            .order_by(Visit.visit_date.desc())
        ).first()

        if not latest_visit:
            return False

        now = datetime.utcnow()

        completed_models = {
            key: result
            for key, result in model_results.items()
            if result.get("status") == "completed"
            and result.get("severity") in {"low", "medium", "high"}
        }

        if not completed_models:
            return True

        def apply_common(record, result: dict) -> None:
            record.ai_report = assessment_report
            record.created_at = now
            record.prediction_status = "completed"
            record.severity = result.get("severity")
            record.predicted_class = result.get("predicted_class")
            record.confidence = result.get("confidence")
            record.probabilities = result.get("probabilities") or {}
            record.input_snapshot = result.get("input_snapshot") or {}
            record.input_provenance = result.get("input_provenance") or {}
            record.oldest_input_age_days = result.get("oldest_input_age_days")
            record.has_stale_inputs = bool(result.get("has_stale_inputs"))

        if "gdm" in completed_models:
            result = completed_models["gdm"]
            gdm = session.exec(select(GDMAssessment).where(GDMAssessment.visit_id == latest_visit.id)).first()
            if not gdm:
                gdm = GDMAssessment(visit_id=latest_visit.id)
            apply_common(gdm, result)
            gdm_risk = _to_gdm_risk_value(result.get("severity"))
            if gdm_risk is not None:
                gdm.risk_level = gdm_risk
            session.add(gdm)

        if "anemia" in completed_models:
            result = completed_models["anemia"]
            anemia = session.exec(select(AnemiaAssessment).where(AnemiaAssessment.visit_id == latest_visit.id)).first()
            if not anemia:
                anemia = AnemiaAssessment(visit_id=latest_visit.id)
            apply_common(anemia, result)
            anemia.diagnosis = result.get("outcome") or result.get("predicted_class")
            session.add(anemia)

        if "preeclampsia" in completed_models:
            result = completed_models["preeclampsia"]
            mha = session.exec(select(MaternalHealthAssessment).where(MaternalHealthAssessment.visit_id == latest_visit.id)).first()
            if not mha:
                mha = MaternalHealthAssessment(visit_id=latest_visit.id)
            apply_common(mha, result)
            preec_risk = _to_gdm_risk_value(result.get("severity"))
            if preec_risk is not None:
                mha.risk_level = preec_risk
            session.add(mha)

        if "fetal" in completed_models:
            result = completed_models["fetal"]
            fetal = session.exec(select(FetalHealthAssessment).where(FetalHealthAssessment.visit_id == latest_visit.id)).first()
            if not fetal:
                fetal = FetalHealthAssessment(visit_id=latest_visit.id)
            apply_common(fetal, result)
            fetal_status = result.get("class_value")
            if fetal_status not in {1, 2, 3}:
                fetal_status = _to_fetal_status_value(result.get("severity"))
            if fetal_status is not None:
                fetal.status = fetal_status
            session.add(fetal)

        session.flush()
        recompute_patient_risk(
            session,
            patient,
            visit_id=latest_visit.id,
            assessment_type=assessment_type,
            record_history=True,
            assessed_at=now,
        )
        session.commit()

        return True

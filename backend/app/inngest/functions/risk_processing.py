"""Risk processing Inngest function."""

import logging
from typing import Any
import inngest
from app.inngest.client import inngest_client

logger = logging.getLogger(__name__)


@inngest_client.create_function(
    fn_id="risk_processing",
    trigger=inngest.TriggerEvent(event="risk/process"),
)
async def risk_processing(ctx: inngest.Context):
    """
    Background job for processing medical risk assessments.
    
    Triggered by: risk/process event
    """
    job_id = ctx.event.data.get("job_id")
    model = ctx.event.data.get("model")
    features = ctx.event.data.get("features", {})

    logger.info(f"Processing job {job_id} using model: {model}")
    
    def to_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    glucose = to_float(features.get("glucose_level"))
    ogtt = to_float(features.get("ogtt"))
    sys_bp = to_float(features.get("blood_pressure_systolic"))
    dia_bp = to_float(features.get("blood_pressure_diastolic"))
    bmi = to_float(features.get("bmi"))
    hgb = to_float(features.get("hgb"))
    fetal_status = to_float(features.get("fetal_health_status"))

    risk_score = 0
    triggered_signals: list[str] = []

    glucose_proxy = glucose if glucose is not None else ogtt
    if glucose_proxy is not None:
        if glucose_proxy >= 180:
            risk_score += 3
            triggered_signals.append("severely elevated glucose")
        elif glucose_proxy >= 140:
            risk_score += 2
            triggered_signals.append("elevated glucose")
        elif glucose_proxy >= 95:
            risk_score += 1
            triggered_signals.append("borderline glucose")

    if sys_bp is not None and dia_bp is not None:
        if sys_bp >= 160 or dia_bp >= 110:
            risk_score += 3
            triggered_signals.append("severe hypertension")
        elif sys_bp >= 140 or dia_bp >= 90:
            risk_score += 2
            triggered_signals.append("hypertension")
        elif sys_bp >= 130 or dia_bp >= 80:
            risk_score += 1
            triggered_signals.append("borderline blood pressure")

    if bmi is not None:
        if bmi >= 35:
            risk_score += 2
            triggered_signals.append("class II obesity")
        elif bmi >= 30:
            risk_score += 1
            triggered_signals.append("obesity")

    if hgb is not None:
        if hgb < 9:
            risk_score += 3
            triggered_signals.append("severe anemia")
        elif hgb < 11:
            risk_score += 2
            triggered_signals.append("anemia")

    if fetal_status is not None:
        if fetal_status >= 3:
            risk_score += 3
            triggered_signals.append("pathological fetal status")
        elif fetal_status >= 2:
            risk_score += 2
            triggered_signals.append("suspect fetal status")

    if risk_score >= 6:
        risk_level = "High"
    elif risk_score >= 3:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    provided_feature_count = sum(
        1 for v in [glucose, ogtt, sys_bp, dia_bp, bmi, hgb, fetal_status] if v is not None
    )
    confidence = min(0.99, 0.5 + (provided_feature_count * 0.06))

    if triggered_signals:
        explanation = f"Rule-based {model} risk assessment using signals: {', '.join(triggered_signals)}."
    else:
        explanation = f"Rule-based {model} risk assessment with no high-risk signals detected."

    result = {
        "job_id": job_id,
        "model": model,
        "risk_level": risk_level,
        "confidence": round(confidence, 2),
        "explanation": explanation,
        "risk_score": risk_score,
    }

    logger.info(f"Completed job {job_id}")
    return result

"""
Persisted storage for assessment results and Inngest fallback queue.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from app.db.session import engine
from app.models.assessment_job import AssessmentJobState, InngestFallbackEvent

ASSESSMENT_STEPS: List[str] = [
    "Analyzing request",
    "Loading patient data",
    "Running maternal health models",
    "Running fetal health models",
    "Retrieving medical guidelines",
    "Generating assessment report",
]


def _now() -> datetime:
    return datetime.utcnow()


def _upsert_state(assessment_id: str, payload: Dict[str, Any]) -> None:
    with Session(engine) as session:
        row = session.get(AssessmentJobState, assessment_id)
        if row is None:
            row = AssessmentJobState(assessment_id=assessment_id, status=payload.get("status", "processing"), payload=payload)
            session.add(row)
        else:
            row.status = payload.get("status", row.status)
            row.payload = payload
            row.updated_at = _now()
            session.add(row)
        session.commit()


def store_assessment_result(assessment_id: str, result: Dict[str, Any]) -> None:
    """Store assessment result."""
    payload = {
        **result,
        "completed_at": datetime.now().isoformat(),
        "status": "completed",
        "current_step": len(ASSESSMENT_STEPS),
        "total_steps": len(ASSESSMENT_STEPS),
        "step_label": "Complete",
        "completed_steps": list(ASSESSMENT_STEPS),
    }
    _upsert_state(assessment_id, payload)


def get_assessment_result(assessment_id: str) -> Optional[Dict[str, Any]]:
    """Get assessment result if available."""
    with Session(engine) as session:
        row = session.get(AssessmentJobState, assessment_id)
        if not row:
            return None
        return dict(row.payload)


def mark_assessment_processing(assessment_id: str) -> None:
    """Mark assessment as processing."""
    payload = {
        "status": "processing",
        "started_at": datetime.now().isoformat(),
        "current_step": 0,
        "total_steps": len(ASSESSMENT_STEPS),
        "step_label": "Starting...",
        "completed_steps": [],
    }
    _upsert_state(assessment_id, payload)


def update_assessment_progress(assessment_id: str, step_number: int, step_label: str) -> None:
    """Update the live progress of a running assessment."""
    with Session(engine) as session:
        row = session.get(AssessmentJobState, assessment_id)
        if row is None:
            return
        data = dict(row.payload)
        data["current_step"] = step_number
        data["total_steps"] = len(ASSESSMENT_STEPS)
        data["step_label"] = step_label
        data["completed_steps"] = ASSESSMENT_STEPS[: max(step_number - 1, 0)]
        row.payload = data
        row.updated_at = _now()
        session.add(row)
        session.commit()


def clear_old_results() -> None:
    """Clear completed results older than 7 days (best-effort maintenance)."""
    cutoff = _now()
    from datetime import timedelta

    cutoff = cutoff - timedelta(days=7)
    with Session(engine) as session:
        rows = session.exec(
            select(AssessmentJobState).where(AssessmentJobState.updated_at < cutoff)
        ).all()
        for r in rows:
            if (r.payload or {}).get("status") == "completed":
                session.delete(r)
        session.commit()


def queue_inngest_event(event_data: Dict[str, Any]) -> None:
    """Queue a failed Inngest event for retry."""
    row = InngestFallbackEvent(
        event_data={**event_data, "queued_at": datetime.now().isoformat(), "retry_count": 0},
    )
    with Session(engine) as session:
        session.add(row)
        session.commit()


def get_fallback_queue_size() -> int:
    """Get number of queued events."""
    with Session(engine) as session:
        return len(session.exec(select(InngestFallbackEvent)).all())


def get_next_queued_event() -> Optional[Dict[str, Any]]:
    """Get and remove the next event from the fallback queue."""
    with Session(engine) as session:
        row = session.exec(select(InngestFallbackEvent).order_by(InngestFallbackEvent.id)).first()
        if not row:
            return None
        data = dict(row.event_data)
        session.delete(row)
        session.commit()
        return data


def get_all_queued_events() -> list:
    """Get all queued events without removing them."""
    with Session(engine) as session:
        rows = session.exec(select(InngestFallbackEvent).order_by(InngestFallbackEvent.id)).all()
        return [dict(r.event_data) for r in rows]

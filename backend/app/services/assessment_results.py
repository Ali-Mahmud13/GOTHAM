"""
In-memory storage for assessment results.
In production, this should use a database like Redis or PostgreSQL.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import deque

# In-memory storage (will be lost on server restart)
# In production, use Redis or a database
_assessment_results: Dict[str, Dict[str, Any]] = {}

# Fallback queue for failed Inngest events (will be lost on server restart)
# In production, use Redis, RabbitMQ, or a database queue
_inngest_fallback_queue: deque = deque(maxlen=1000)

ASSESSMENT_STEPS: List[str] = [
    "Analyzing request",
    "Loading patient data",
    "Running maternal health models",
    "Running fetal health models",
    "Retrieving medical guidelines",
    "Generating assessment report",
]


def store_assessment_result(assessment_id: str, result: Dict[str, Any]) -> None:
    """Store assessment result."""
    _assessment_results[assessment_id] = {
        **result,
        "completed_at": datetime.now().isoformat(),
        "status": "completed",
        "current_step": len(ASSESSMENT_STEPS),
        "total_steps": len(ASSESSMENT_STEPS),
        "step_label": "Complete",
        "completed_steps": list(ASSESSMENT_STEPS),
    }


def get_assessment_result(assessment_id: str) -> Optional[Dict[str, Any]]:
    """Get assessment result if available."""
    return _assessment_results.get(assessment_id)


def mark_assessment_processing(assessment_id: str) -> None:
    """Mark assessment as processing."""
    _assessment_results[assessment_id] = {
        "status": "processing",
        "started_at": datetime.now().isoformat(),
        "current_step": 0,
        "total_steps": len(ASSESSMENT_STEPS),
        "step_label": "Starting...",
        "completed_steps": [],
    }


def update_assessment_progress(
    assessment_id: str,
    step_number: int,
    step_label: str,
) -> None:
    """Update the live progress of a running assessment."""
    entry = _assessment_results.get(assessment_id)
    if entry is None:
        return
    entry["current_step"] = step_number
    entry["total_steps"] = len(ASSESSMENT_STEPS)
    entry["step_label"] = step_label
    entry["completed_steps"] = ASSESSMENT_STEPS[: step_number - 1]


def clear_old_results() -> None:
    """Clear results (for cleanup)."""
    _assessment_results.clear()


def queue_inngest_event(event_data: Dict[str, Any]) -> None:
    """Queue a failed Inngest event for retry."""
    _inngest_fallback_queue.append({
        **event_data,
        "queued_at": datetime.now().isoformat(),
        "retry_count": 0
    })


def get_fallback_queue_size() -> int:
    """Get number of queued events."""
    return len(_inngest_fallback_queue)


def get_next_queued_event() -> Optional[Dict[str, Any]]:
    """Get and remove the next event from the fallback queue."""
    if _inngest_fallback_queue:
        return _inngest_fallback_queue.popleft()
    return None


def get_all_queued_events() -> list:
    """Get all queued events without removing them."""
    return list(_inngest_fallback_queue)

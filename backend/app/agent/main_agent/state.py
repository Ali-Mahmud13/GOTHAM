from langgraph.graph import MessagesState
from typing import Optional, Literal, Callable
from contextvars import ContextVar

class AgentState(MessagesState):
    # Clarity check fields
    incomplete: Optional[Literal["yes", "no"]] = None
    inscope: Optional[Literal["yes", "no"]] = None
    clear: Optional[Literal["yes", "no"]] = None
    
    # Prediction and routing fields
    prediction_decision: Optional[Literal["both", "maternal", "fetal", "rag", "respond"]] = None
    should_retrieve_decision: Optional[Literal["load", "not_load"]] = None
    
    # Patient tracking
    current_patient_id: Optional[str] = None
    patient_identifier: Optional[str] = None
    patient_data: Optional[dict] = None
    
    # Reports and context (persist across conversation)
    maternal_report: Optional[str] = None
    fetal_report: Optional[str] = None
    ultrasound_report: Optional[str] = None
    annotated_ultrasound_image_url: Optional[str] = None
    rag_context: Optional[str] = None
    rag_keywords: Optional[str] = None

    # Latest assessment payload for persistence (per run)
    assessment_type_to_save: Optional[str] = None
    assessment_report_to_save: Optional[str] = None
    assessment_risk_levels: Optional[dict] = None


_progress_callback_var: ContextVar[Optional[Callable[[int, str], None]]] = ContextVar(
    "_progress_callback_var", default=None
)


def set_progress_callback(cb: Optional[Callable[[int, str], None]]) -> None:
    """Set the progress callback for the current async context."""
    _progress_callback_var.set(cb)


def report_progress(step_number: int, label: str) -> None:
    """Fire the progress callback if one is set in the current context."""
    cb = _progress_callback_var.get()
    if cb is not None:
        try:
            cb(step_number, label)
        except Exception:
            pass
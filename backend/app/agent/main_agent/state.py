from langgraph.graph import MessagesState
from typing import Optional, Literal

class AgentState(MessagesState):
    # Clarity check fields
    incomplete: Optional[Literal["yes", "no"]] = None
    inscope: Optional[Literal["yes", "no"]] = None
    clear: Optional[Literal["yes", "no"]] = None
    
    # Prediction and routing fields
    prediction_decision: Optional[Literal["both", "maternal", "fetal", "rag", "respond"]] = None
    should_retrieve_decision: Optional[Literal["retrieve", "not_retrieve"]] = None
    
    # Patient tracking
    current_patient_id: Optional[str] = None
    patient_identifier: Optional[str] = None
    patient_data: Optional[dict] = None
    
    # Reports and context (persist across conversation)
    maternal_report: Optional[str] = None
    fetal_report: Optional[str] = None
    rag_context: Optional[str] = None
    rag_keywords: Optional[str] = None
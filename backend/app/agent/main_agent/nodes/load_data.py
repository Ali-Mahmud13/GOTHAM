from langchain_core.messages import HumanMessage
from ..state import AgentState, report_progress
from ..system_prompt import PATIENT_ID_EXTRACTION_PROMPT
from app.core.llm import get_llm
from app.services.patient_service import get_patient_service
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _extract_patient_id_regex(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"\bP\s*0*(\d+)\b", text, re.IGNORECASE)
    if not m:
        m = re.search(r"\(\s*P\s*0*(\d+)\s*\)", text, re.IGNORECASE)
    if not m:
        return None
    return f"P{int(m.group(1)):03d}"

def _normalize_patient_identifier(raw_value: str | None) -> str:
    if not raw_value:
        return "NONE"
    val = str(raw_value).strip().strip("`\"' ")
    regex_id = _extract_patient_id_regex(val)
    if regex_id:
        return regex_id
    if val.startswith("(") and val.endswith(")"):
        val = val[1:-1].strip()
    return val if val else "NONE"

async def load_data_node(state: AgentState) -> AgentState:
    report_progress(2, "Loading patient data")
    llm = get_llm(temperature=0)
    if state.get("prediction_decision") in {"maternal", "fetal", "both"}:
        state["model_results"] = {}
        state["maternal_report"] = None
        state["fetal_report"] = None
    
    user_message = state["messages"][-1].content
    current_patient_id = state.get("current_patient_id")
    
    logger.info("="*60)
    logger.info("LOAD DATA - Starting")
    logger.info("="*60)
    logger.info(f"Current patient ID in state: {current_patient_id}")
    
    conversation_history = "\n".join([
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in state["messages"][:-1]
    ])
    
    prompt = PATIENT_ID_EXTRACTION_PROMPT.format(
        conversation_history=conversation_history,
        user_message=user_message,
        current_patient_id=current_patient_id or "None"
    )
    
    patient_identifier = _extract_patient_id_regex(user_message)

    if not patient_identifier:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        patient_identifier = _normalize_patient_identifier(response.content)
    else:
        logger.info(f"Regex extracted patient ID from message: {patient_identifier}")
    
    logger.info(f"Final extracted patient identifier: {patient_identifier}")
    state["patient_identifier"] = patient_identifier
    
    # Check if this is a new patient
    if patient_identifier != "NONE" and patient_identifier != current_patient_id:
        logger.info(f"New patient detected! Clearing old reports for previous patient: {current_patient_id}")
        state["current_patient_id"] = patient_identifier
        state["maternal_report"] = None
        state["fetal_report"] = None
        logger.info(f"Updated current_patient_id to: {patient_identifier}")
    
    # Fetch patient data using patient service (OPTIMIZED - uses materialized table)
    patient_service = get_patient_service()
    patient_data = await patient_service.get_patient_data_optimized(patient_identifier)
    
    if patient_data:
        state["patient_data"] = patient_data
        # Canonicalize to the real Patient_ID so downstream persistence always saves correctly,
        # even when we resolved the patient from a name/typo ("ariana frande" → P###).
        canonical_id = patient_data.get("Patient_ID")
        if canonical_id:
            state["patient_identifier"] = canonical_id
            state["current_patient_id"] = canonical_id
        logger.info(f"Patient data loaded successfully for: {patient_identifier}")
    else:
        logger.warning(f"No patient data found for: {patient_identifier}")
        state["patient_data"] = {}
    
    logger.info("="*60 + "\n")
    
    return state

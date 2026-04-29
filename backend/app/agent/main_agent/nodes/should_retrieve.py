from langchain_core.messages import HumanMessage
from ..state import AgentState
from ..system_prompt import SHOULD_RETRIEVE_PROMPT
from app.core.llm import get_llm
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def should_retrieve_node(state: AgentState) -> AgentState:
    llm = get_llm(temperature=0)
    
    user_message = state["messages"][-1].content
    
    logger.info("="*60)
    logger.info("SHOULD LOAD PATIENT - Checking if patient data needs loading")
    logger.info("="*60)
    logger.info(f"User message: '{user_message}'")
    
    conversation_history = "\n".join([
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in state["messages"][:-1]
    ])
    
    current_patient_id = state.get("current_patient_id", "None")
    has_patient_data = "yes" if state.get("patient_data") else "no"
    
    # Prepare patient data summary
    patient_data_summary = ""
    if state.get("patient_data"):
        patient_data = state["patient_data"]
        patient_data_summary = f"Patient ID: {patient_data.get('Patient_ID', 'N/A')}, Name: {patient_data.get('Name', 'N/A')}, Age: {patient_data.get('Age', 'N/A')}"
    
    logger.info(f"Current state:")
    logger.info(f"  - current_patient_id: {current_patient_id}")
    logger.info(f"  - has_patient_data: {has_patient_data}")
    if patient_data_summary:
        logger.info(f"  - patient_data_summary: {patient_data_summary}")
    
    prompt = SHOULD_RETRIEVE_PROMPT.format(
        user_message=user_message,
        conversation_history=conversation_history,
        current_patient_id=current_patient_id,
        has_patient_data=has_patient_data,
        patient_data_summary=patient_data_summary
    )
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    decision = response.content.strip().lower()
    
    logger.info(f"LLM response: '{response.content}'")
    
    # Validate and normalize the decision
    valid_decisions = ["load", "not_load"]
    
    # Try to normalize common variations
    decision_lower = decision.lower()
    if "load" in decision_lower and "not" not in decision_lower:
        decision = "load"
    elif "not_load" in decision_lower or "not load" in decision_lower or "dont_load" in decision_lower:
        decision = "not_load"
    elif "no" in decision_lower or "skip" in decision_lower:
        decision = "not_load"
    elif "yes" in decision_lower or "do" in decision_lower:
        decision = "load"
    
    # Final validation
    if decision not in valid_decisions:
        logger.warning(f"Invalid response '{decision}', analyzing message for patient reference")
        # Simple heuristic: if message contains patient ID pattern, default to load
        import re
        if re.search(r'P\d{3}', user_message) or "patient" in user_message.lower():
            decision = "load"
        else:
            decision = "not_load"
    
    # Store decision
    state["should_load_patient"] = decision
    state["needs_patient_data"] = (decision == "load")
    
    logger.info(f"Decision: {decision}")
    logger.info(f"Needs patient data: {state['needs_patient_data']}")
    logger.info("="*60 + "\n")
    
    return state
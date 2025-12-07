from langchain_core.messages import HumanMessage
from ..state import AgentState
from ..system_prompt import PATIENT_ID_EXTRACTION_PROMPT
from app.core.llm import get_llm
from app.services.patient_service import get_patient_service
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def load_data_node(state: AgentState) -> AgentState:
    llm = get_llm(temperature=0)
    
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
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    patient_idenifier = response.content.strip()
    
    logger.info(f"Extracted patient ID: {patient_idenifier}")
    
    state["patient_identifier"] = patient_idenifier
    
    # Check if this is a new patient
    if patient_idenifier != "NONE" and patient_idenifier != current_patient_id:
        logger.info(f"New patient detected! Clearing old reports for previous patient: {current_patient_id}")
        state["current_patient_id"] = patient_idenifier
        state["maternal_report"] = None
        state["fetal_report"] = None
        logger.info(f"Updated current_patient_id to: {patient_idenifier}")
    
    # Fetch patient data using patient service
    patient_service = get_patient_service()
    patient_data = await patient_service.get_patient_data(patient_idenifier)
    
    if patient_data:
        state["patient_data"] = patient_data
        logger.info(f"Patient data loaded successfully for: {patient_idenifier}")
    else:
        logger.warning(f"No patient data found for: {patient_idenifier}")
        state["patient_data"] = {}
    
    logger.info("="*60 + "\n")
    
    return state
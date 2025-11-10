from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from ..state import AgentState
from ..system_prompt import PATIENT_ID_EXTRACTION_PROMPT
from ...data_temp.fetch_data import fetch_patient_data
from config import GROQ_API_KEY, MODEL_NAME
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def load_data_node(state: AgentState) -> AgentState:
    llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0)
    
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
    patient_id = response.content.strip()
    
    logger.info(f"Extracted patient ID: {patient_id}")
    
    state["patient_identifier"] = patient_id
    
    # Check if this is a new patient
    if patient_id != "NONE" and patient_id != current_patient_id:
        logger.info(f"New patient detected! Clearing old reports for previous patient: {current_patient_id}")
        state["current_patient_id"] = patient_id
        state["maternal_report"] = None
        state["fetal_report"] = None
        logger.info(f"Updated current_patient_id to: {patient_id}")
    
    # Fetch patient data
    patient_data = await fetch_patient_data(patient_id)
    
    if patient_data:
        state["patient_data"] = patient_data
        logger.info(f"Patient data loaded successfully for: {patient_id}")
    else:
        logger.warning(f"No patient data found for: {patient_id}")
        state["patient_data"] = {}
    
    logger.info("="*60 + "\n")
    
    return state
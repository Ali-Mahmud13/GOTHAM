from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from ..state import AgentState
from ..system_prompt import SHOULD_RETRIEVE_PROMPT
from config import GROQ_API_KEY, MODEL_NAME
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def should_retrieve_node(state: AgentState) -> AgentState:
    llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0)
    
    user_message = state["messages"][-1].content
    
    logger.info("="*60)
    logger.info("SHOULD RETRIEVE - Checking if new retrieval needed")
    logger.info("="*60)
    logger.info(f"User message: '{user_message}'")
    
    conversation_history = "\n".join([
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in state["messages"][:-1]
    ])
    
    has_patient_data = "yes" if state.get("patient_data") else "no"
    has_maternal_report = "yes" if state.get("maternal_report") else "no"
    has_fetal_report = "yes" if state.get("fetal_report") else "no"
    has_rag_context = "yes" if state.get("rag_context") else "no"
    
    # Prepare summaries
    patient_data_summary = ""
    if state.get("patient_data"):
        patient_data = state["patient_data"]
        patient_data_summary = f"Patient ID: {patient_data.get('Patient_ID', 'N/A')}, Age: {patient_data.get('Age', 'N/A')}, BMI: {patient_data.get('BMI', 'N/A')}"
    
    rag_context_preview = ""
    if state.get("rag_context"):
        rag_context_preview = state["rag_context"][:500] + "..." if len(state["rag_context"]) > 500 else state["rag_context"]
    
    logger.info(f"Available data:")
    logger.info(f"  - has_patient_data: {has_patient_data}")
    logger.info(f"  - has_maternal_report: {has_maternal_report}")
    logger.info(f"  - has_fetal_report: {has_fetal_report}")
    logger.info(f"  - has_rag_context: {has_rag_context}")
    
    prompt = SHOULD_RETRIEVE_PROMPT.format(
        user_message=user_message,
        conversation_history=conversation_history,
        has_patient_data=has_patient_data,
        has_maternal_report=has_maternal_report,
        has_fetal_report=has_fetal_report,
        has_rag_context=has_rag_context,
        patient_data_summary=patient_data_summary,
        rag_context_preview=rag_context_preview
    )
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    decision = response.content.strip().lower()
    
    logger.info(f"LLM response: '{response.content}'")
    
    # Validate
    if decision not in ["retrieve", "not_retrieve"]:
        logger.warning(f"Invalid response '{decision}', defaulting to 'not_retrieve'")
        decision = "not_retrieve"
    
    state["should_retrieve_decision"] = decision
    logger.info(f"Decision: {decision}")
    logger.info("="*60 + "\n")
    
    return state
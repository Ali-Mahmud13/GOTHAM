from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from ..state import AgentState
from ..system_prompt import PREDICTION_DECISION_PROMPT
from config import GROQ_API_KEY, MODEL_NAME
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def prediction_decision_node(state: AgentState) -> AgentState:
    llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0)
    
    user_message = state["messages"][-1].content
    
    logger.info("="*60)
    logger.info("PREDICTION DECISION - Starting Analysis")
    logger.info("="*60)
    logger.info(f"User message: '{user_message}'")
    
    # Gather state context
    current_patient_id = state.get("current_patient_id", "None")
    has_maternal_report = "yes" if state.get("maternal_report") else "no"
    has_fetal_report = "yes" if state.get("fetal_report") else "no"
    has_patient_data = "yes" if state.get("patient_data") else "no"
    has_rag_context = "yes" if state.get("rag_context") else "no"
    
    logger.info(f"State Context:")
    logger.info(f"  - current_patient_id: {current_patient_id}")
    logger.info(f"  - has_maternal_report: {has_maternal_report}")
    logger.info(f"  - has_fetal_report: {has_fetal_report}")
    logger.info(f"  - has_patient_data: {has_patient_data}")
    logger.info(f"  - has_rag_context: {has_rag_context}")
    
    conversation_history = "\n".join([
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in state["messages"][:-1]
    ])
    
    prompt = PREDICTION_DECISION_PROMPT.format(
        current_patient_id=current_patient_id,
        has_maternal_report=has_maternal_report,
        has_fetal_report=has_fetal_report,
        has_patient_data=has_patient_data,
        has_rag_context=has_rag_context,
        conversation_history=conversation_history,
        user_message=user_message
    )
    
    logger.info("Sending to LLM for classification...")
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    decision = response.content.strip().lower()
    
    logger.info(f"LLM raw response: '{response.content}'")
    
    # Validate decision
    valid_decisions = ["maternal", "fetal", "both", "rag", "respond"]
    if decision not in valid_decisions:
        logger.warning(f"Invalid decision '{decision}', defaulting to 'respond'")
        decision = "respond"
    
    state["prediction_decision"] = decision
    logger.info(f"Final decision: '{decision}'")
    
    # Log routing
    route_map = {
        "maternal": "LOAD_DATA → RUN_MATERNAL → GENERATE_KEYWORDS → RAG_RETRIEVAL → RESPOND",
        "fetal": "LOAD_DATA → RUN_FETAL → GENERATE_KEYWORDS → RAG_RETRIEVAL → RESPOND",
        "both": "LOAD_DATA → RUN_MATERNAL → RUN_FETAL → GENERATE_KEYWORDS → RAG_RETRIEVAL → RESPOND",
        "rag": "RAG_RETRIEVAL (direct) → RESPOND",
        "respond": "SHOULD_RETRIEVE → (maybe RAG_RETRIEVAL) → RESPOND"
    }
    logger.info(f"Route: {route_map.get(decision, 'UNKNOWN')}")
    logger.info("="*60 + "\n")
    
    return state
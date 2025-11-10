from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..state import AgentState
from ..system_prompt import (
    SYSTEM_PROMPT, 
    RAG_RESPONSE_PROMPT, 
    ASSESSMENT_RESPONSE_PROMPT,
    RESPOND_PROMPT
)
from config import GROQ_API_KEY, MODEL_NAME
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def respond_node(state: AgentState) -> AgentState:
    llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0.3)
    
    prediction_decision = state.get("prediction_decision")
    
    logger.info("="*60)
    logger.info("RESPOND NODE - Generating Response")
    logger.info("="*60)
    logger.info(f"Prediction decision: {prediction_decision}")
    
    user_message = state["messages"][-1].content
    conversation_history = "\n".join([
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in state["messages"][:-1]
    ])
    
    # Case 1: Assessment response (maternal/fetal/both)
    if prediction_decision in ["maternal", "fetal", "both"]:
        logger.info("Response type: Health Assessment Report")
        
        maternal_report = state.get("maternal_report", "") or "Not assessed"
        fetal_report = state.get("fetal_report", "") or "Not assessed"
        rag_context = state.get("rag_context", "") or "No additional guidance available"
        patient_data = state.get("patient_data", {})
        
        patient_data_str = "\n".join([f"{k}: {v}" for k, v in patient_data.items()]) if patient_data else "Not available"
        
        response_prompt = ASSESSMENT_RESPONSE_PROMPT.format(
            maternal_report=maternal_report,
            fetal_report=fetal_report,
            rag_context=rag_context,
            patient_data=patient_data_str
        )
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
            HumanMessage(content=response_prompt)
        ]
    
    # Case 2: RAG response (medical knowledge query)
    elif prediction_decision == "rag":
        logger.info("Response type: Medical Knowledge Query")
        
        rag_context = state.get("rag_context", "") or "No context retrieved"
        maternal_report = state.get("maternal_report", "") or ""
        fetal_report = state.get("fetal_report", "") or ""
        
        response_prompt = RAG_RESPONSE_PROMPT.format(
            rag_context=rag_context,
            maternal_report=maternal_report if maternal_report else "N/A",
            fetal_report=fetal_report if fetal_report else "N/A",
            user_question=user_message
        )
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
            HumanMessage(content=response_prompt)
        ]
    
    # Case 3: Respond (followup/clarification/casual)
    else:
        logger.info("Response type: Followup/Clarification/Casual")
        
        # Prepare context summary
        context_parts = []
        
        if state.get("patient_data"):
            patient_data = state["patient_data"]
            context_parts.append(f"Patient Data: {patient_data}")
        
        if state.get("maternal_report"):
            context_parts.append(f"Maternal Report Available: Yes")
        
        if state.get("fetal_report"):
            context_parts.append(f"Fetal Report Available: Yes")
        
        if state.get("rag_context"):
            context_parts.append(f"RAG Context Available: Yes")
        
        context_summary = "\n".join(context_parts) if context_parts else "No specific context available"
        
        response_prompt = RESPOND_PROMPT.format(
            context_summary=context_summary,
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
            HumanMessage(content=response_prompt)
        ]
    
    logger.info("Sending to LLM for response generation...")
    response = await llm.ainvoke(messages)
    
    state["messages"].append(AIMessage(content=response.content))
    logger.info(f"Response generated (length: {len(response.content)} chars)")
    
    # Reset per-message state
    reset_state(state)
    
    logger.info("="*60 + "\n")
    
    return state


def reset_state(state: AgentState):
    """Reset per-message state fields, keep conversation-persistent data"""
    logger.info("Resetting per-message state fields")
    
    # Reset clarity checks
    state["incomplete"] = None
    state["inscope"] = None
    state["clear"] = None
    
    # Reset decision
    state["prediction_decision"] = None
    
    # Reset temporary extraction
    state["patient_identifier"] = None
    
    # Reset retrieval decisions
    if "should_retrieve_decision" in state:
        state["should_retrieve_decision"] = None
    if "rag_keywords" in state:
        state["rag_keywords"] = None
    
    # Keep persistent: messages, current_patient_id, patient_data, maternal_report, fetal_report, rag_context
    
    logger.info("State reset complete")
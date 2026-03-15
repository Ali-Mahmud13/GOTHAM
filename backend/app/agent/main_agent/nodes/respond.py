from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..state import AgentState
from ..system_prompt import (
    SYSTEM_PROMPT, 
    RAG_RESPONSE_PROMPT, 
    ASSESSMENT_RESPONSE_PROMPT,
    RESPOND_PROMPT
)
from app.core.llm import get_llm
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _extract_maternal_risk_levels(maternal_report: str) -> dict:
    risks = {"gdm": "unknown", "anemia": "unknown"}

    report_lower = maternal_report.lower()

    if "high risk of gestational diabetes" in report_lower:
        risks["gdm"] = "high"
    elif "low risk of gestational diabetes" in report_lower:
        risks["gdm"] = "low"
    elif "risk level" in report_lower and "gestational" in report_lower:
        # Fallback when a textual risk level appears near gestational content.
        m = re.search(r"risk level\s*[:\-]\s*(high|medium|elevated|low)", report_lower)
        if m:
            risks["gdm"] = "medium" if m.group(1) == "elevated" else m.group(1)

    if any(k in report_lower for k in ["severe anemia", "moderate anemia", "iron deficiency anemia"]):
        if "severe anemia" in report_lower:
            risks["anemia"] = "high"
        elif "moderate anemia" in report_lower or "iron deficiency anemia" in report_lower:
            risks["anemia"] = "medium"
    elif "no anemia" in report_lower or "normal hemoglobin" in report_lower:
        risks["anemia"] = "low"

    return risks


def _extract_fetal_risk_level(fetal_report: str) -> str:
    m = re.search(r"Fetal\s+Status\s*:\s*(Normal|Suspect|Pathological)", fetal_report, re.IGNORECASE)
    if m:
        status = m.group(1).lower()
        if status == "normal":
            return "low"
        if status == "suspect":
            return "medium"
        if status == "pathological":
            return "high"

    m_numeric = re.search(r"Risk\s+Level\s*:\s*([123])", fetal_report, re.IGNORECASE)
    if m_numeric:
        return {"1": "low", "2": "medium", "3": "high"}.get(m_numeric.group(1), "unknown")

    return "unknown"


def _build_assessment_report_payload(assessment_type: str, maternal_report: str, fetal_report: str) -> tuple[str, dict]:
    maternal_risks = _extract_maternal_risk_levels(maternal_report)
    fetal_risk = _extract_fetal_risk_level(fetal_report)

    sections = [f"## Assessment Type\n{assessment_type}"]
    risk_levels = {"gdm": None, "anemia": None, "fetal": None}

    if assessment_type in ["maternal", "both"] and maternal_report and maternal_report != "Not assessed":
        risk_levels["gdm"] = maternal_risks["gdm"]
        risk_levels["anemia"] = maternal_risks["anemia"]
        sections.append(
            "## Maternal Assessments\n"
            f"- Gestational Diabetes Risk Level: {maternal_risks['gdm']}\n"
            f"- Maternal Anemia Risk Level: {maternal_risks['anemia']}\n\n"
            "### AI Generated Report\n"
            f"{maternal_report}"
        )

    if assessment_type in ["fetal", "both"] and fetal_report and fetal_report != "Not assessed":
        risk_levels["fetal"] = fetal_risk
        sections.append(
            "## Fetal Assessment\n"
            f"- Fetal Risk Level: {fetal_risk}\n\n"
            "### AI Generated Report\n"
            f"{fetal_report}"
        )

    return "\n\n".join(sections), risk_levels

async def respond_node(state: AgentState) -> AgentState:
    llm = get_llm(temperature=0.3)
    state["assessment_type_to_save"] = None
    state["assessment_report_to_save"] = None
    state["assessment_risk_levels"] = None
    
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
        rag_context = state.get("rag_context", "") or "No Docuemnts available"
        patient_data = state.get("patient_data", {})
        assessment= state.get("prediction_decision", {})
        
        patient_data_str = "\n".join([f"{k}: {v}" for k, v in patient_data.items()]) if patient_data else "Not available"

        assessment_report_payload, risk_levels = _build_assessment_report_payload(
            prediction_decision,
            maternal_report,
            fetal_report,
        )
        state["assessment_type_to_save"] = prediction_decision
        state["assessment_report_to_save"] = assessment_report_payload
        state["assessment_risk_levels"] = risk_levels
        
        response_prompt = ASSESSMENT_RESPONSE_PROMPT.format(
            maternal_report=maternal_report,
            fetal_report=fetal_report,
            rag_context=rag_context,
            patient_data=patient_data_str,
            assessment_type=assessment
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
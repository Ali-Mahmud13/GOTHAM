from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..state import AgentState, report_progress
from ..system_prompt import (
    SYSTEM_PROMPT, 
    RAG_RESPONSE_PROMPT, 
    ASSESSMENT_RESPONSE_PROMPT,
    RESPOND_PROMPT,
    FOLLOW_UP_QUESTIONS_PROMPT
)
from app.core.llm import get_llm
import logging
import re
import json
import asyncio

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


def _extract_percentage(value: str) -> float | None:
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", value)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _extract_maternal_pipeline_confidence(maternal_report: str) -> float | None:
    gdp_conf = None
    anemia_conf = None

    no_gd = re.search(
        r"Confidence\s*-\s*No\s*GD\s*:\s*([0-9]+(?:\.[0-9]+)?\s*%)",
        maternal_report,
        re.IGNORECASE,
    )
    gd_yes = re.search(
        r"Confidence\s*-\s*GD\s*Present\s*:\s*([0-9]+(?:\.[0-9]+)?\s*%)",
        maternal_report,
        re.IGNORECASE,
    )

    gdp_vals = []
    if no_gd:
        pct = _extract_percentage(no_gd.group(1))
        if pct is not None:
            gdp_vals.append(pct)
    if gd_yes:
        pct = _extract_percentage(gd_yes.group(1))
        if pct is not None:
            gdp_vals.append(pct)
    if gdp_vals:
        gdp_conf = max(gdp_vals)

    anemia_section = re.search(
        r"##\s*Confidence Scores([\s\S]*?)(?:\n---|\Z)",
        maternal_report,
        re.IGNORECASE,
    )
    if anemia_section:
        entries = re.findall(
            r"-\s*\*\*[^*]+\*\*\s*:\s*([0-9]+(?:\.[0-9]+)?\s*%)",
            anemia_section.group(1),
            re.IGNORECASE,
        )
        anemia_vals = []
        for e in entries:
            pct = _extract_percentage(e)
            if pct is not None:
                anemia_vals.append(pct)
        if anemia_vals:
            anemia_conf = max(anemia_vals)

    parts = [x for x in [gdp_conf, anemia_conf] if x is not None]
    if not parts:
        return None

    return sum(parts) / len(parts)


def _extract_fetal_pipeline_confidence(fetal_report: str) -> float | None:
    ctg_conf = None
    us_conf = None

    ctg_vals = []
    for label in ["Normal", "Suspect", "Pathological"]:
        m = re.search(
            rf"{label}\s*:\s*([0-9]+(?:\.[0-9]+)?\s*%)",
            fetal_report,
            re.IGNORECASE,
        )
        if m:
            pct = _extract_percentage(m.group(1))
            if pct is not None:
                ctg_vals.append(pct)
    if ctg_vals:
        ctg_conf = max(ctg_vals)

    us_avg = re.search(
        r"Average\s+Confidence\s*:\s*([0-9]+(?:\.[0-9]+)?\s*%)",
        fetal_report,
        re.IGNORECASE,
    )
    if us_avg:
        pct = _extract_percentage(us_avg.group(1))
        if pct is not None:
            us_conf = pct

    if ctg_conf is not None and us_conf is not None:
        return (0.7 * ctg_conf) + (0.3 * us_conf)
    if ctg_conf is not None:
        return ctg_conf
    if us_conf is not None:
        return us_conf
    return None


def _build_pipeline_confidence_footer(
    prediction_decision: str,
    maternal_report: str,
    fetal_report: str,
) -> str:
    maternal_conf = _extract_maternal_pipeline_confidence(maternal_report)
    fetal_conf = _extract_fetal_pipeline_confidence(fetal_report)

    lines = []

    if prediction_decision in ["maternal", "both"] and maternal_conf is not None:
        lines.append(f"Maternal pipeline confidence: {maternal_conf:.1f}%")

    if prediction_decision in ["fetal", "both"] and fetal_conf is not None:
        lines.append(f"Fetal pipeline confidence: {fetal_conf:.1f}%")

    if not lines:
        return ""

    joined = "<br>".join(lines)
    joined_clean = joined.replace("<br>", "\n")
    return (
        "**Pipeline confidence**\n"
        f"{joined_clean}\n"
        "_Model certainty only, not diagnostic certainty._"
    )


def _extract_ultrasound_image(text: str) -> str | None:
    """Extract image URL from markdown or report text"""
    if not text:
        return None
    # Some reports may contain multiple images (e.g., thumbnails + annotated).
    # Return the most recent match.
    matches = re.findall(r"!\[.*?\]\((.*?)\)", text)
    if matches:
        return matches[-1]
    return None


async def respond_node(state: AgentState) -> AgentState:
    report_progress(6, "Generating assessment report")
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
    
    if prediction_decision in ["maternal", "fetal", "both"]:
        logger.info("Response type: Health Assessment Report")
        
        maternal_report = state.get("maternal_report", "") or "Not assessed"
        fetal_report = state.get("fetal_report", "") or "Not assessed"
        rag_context = state.get("rag_context", "") or "No Docuemnts available"
        patient_data = state.get("patient_data", {})
        assessment = state.get("prediction_decision", {})
        
        patient_data_str = "\n".join([f"{k}: {v}" for k, v in patient_data.items()]) if patient_data else "Not available"

        risk_levels = {
            "gdm": _extract_maternal_risk_levels(maternal_report)["gdm"],
            "anemia": _extract_maternal_risk_levels(maternal_report)["anemia"],
            "fetal": _extract_fetal_risk_level(fetal_report),
        }
        state["assessment_type_to_save"] = prediction_decision
        state["assessment_risk_levels"] = risk_levels
        
        response_prompt = ASSESSMENT_RESPONSE_PROMPT.format(
            maternal_report=maternal_report,
            fetal_report=fetal_report,
            rag_context=rag_context,
            patient_data=patient_data_str,
            assessment_type=assessment
        )
        
        # Keep only the last 4 messages to save tokens and prevent 413 Payload Too Large errors
        recent_messages = state["messages"][-4:] if len(state["messages"]) > 4 else state["messages"]
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *recent_messages,
            HumanMessage(content=response_prompt)
        ]
    
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
        
        # Keep only the last 4 messages to save tokens and prevent 413 Payload Too Large errors
        recent_messages = state["messages"][-4:] if len(state["messages"]) > 4 else state["messages"]
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *recent_messages,
            HumanMessage(content=response_prompt)
        ]
    
    else:
        logger.info("Response type: Followup/Clarification/Casual")
        
        context_parts = []
        if state.get("patient_data"):
            context_parts.append(f"Patient Data: {state['patient_data']}")
        if state.get("maternal_report"):
            context_parts.append("Maternal Report Available: Yes")
        if state.get("fetal_report"):
            context_parts.append("Fetal Report Available: Yes")
        if state.get("rag_context"):
            context_parts.append("RAG Context Available: Yes")
        
        context_summary = "\n".join(context_parts) if context_parts else "No specific context available"
        
        response_prompt = RESPOND_PROMPT.format(
            context_summary=context_summary,
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        # Keep only the last 4 messages to save tokens and prevent 413 Payload Too Large errors
        recent_messages = state["messages"][-4:] if len(state["messages"]) > 4 else state["messages"]
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *recent_messages,
            HumanMessage(content=response_prompt)
        ]
        
    logger.info("Sending to LLM for response generation...")
    response = await llm.ainvoke(messages)
    raw_response = response.content

    # Suggested questions feature has been disabled by user request.
    suggested_questions: list = []

    state["suggested_questions"] = suggested_questions
    if suggested_questions:
        logger.info(f"Suggested questions: {suggested_questions}")

    final_response = raw_response
    if prediction_decision in ["maternal", "fetal", "both"]:
        final_response = _enforce_concise_assessment_output(final_response)
        confidence_footer = _build_pipeline_confidence_footer(
            prediction_decision,
            state.get("maternal_report", "") or "",
            state.get("fetal_report", "") or "",
        )
        if confidence_footer:
            final_response += f"\n\n{confidence_footer}"

    # ✅ ADD: Extract image from stored ultrasound report
    if prediction_decision in ["fetal", "both"]:
        image_url = (
            state.get("annotated_ultrasound_image_url")
            or _extract_ultrasound_image(state.get("ultrasound_report") or "")
            or _extract_ultrasound_image(state.get("fetal_report") or "")
            or (state.get("patient_data") or {}).get("latest_ultrasound_thumbnail_url")
            or (state.get("patient_data") or {}).get("latest_ultrasound_image_url")
        )

        if image_url:
            logger.info(f"✓ Appending ultrasound image: {image_url}")
            final_response += f"\n\n### Fetal Ultrasound Image\n\n![Annotated Ultrasound]({image_url})"
        else:
            logger.info("DEBUG: No ultrasound image URL available to append")

    # ✅ CRITICAL FIX: save the concise final response, not raw payload
    if prediction_decision in ["maternal", "fetal", "both"]:
        state["assessment_report_to_save"] = final_response
    
    state["messages"].append(AIMessage(content=final_response))
    logger.info(f"Response generated (length: {len(final_response)} chars)")
    
    logger.info("="*60 + "\n")
    return state


def reset_state(state: AgentState):
    logger.info("Resetting per-message state fields")
    state["incomplete"] = None
    state["inscope"] = None
    state["clear"] = None
    state["prediction_decision"] = None
    state["patient_identifier"] = None
    # NOTE: suggested_questions is intentionally NOT cleared here.
    # It must survive in the returned graph state so agent_service can read it.
    if "should_retrieve_decision" in state:
        state["should_retrieve_decision"] = None
    if "rag_keywords" in state:
        state["rag_keywords"] = None
    logger.info("State reset complete")


async def persist_node(state: AgentState) -> AgentState:
    """Persist assessment report to database after response is generated."""
    from app.services.assessment_persistence import save_assessment_report
    
    assessment_type_to_save = state.get("assessment_type_to_save")
    assessment_report_to_save = state.get("assessment_report_to_save")
    assessment_risk_levels = state.get("assessment_risk_levels")
    patient_identifier = state.get("patient_identifier")
    
    logger.info("="*60)
    logger.info("PERSIST NODE - Saving Assessment Report")
    logger.info("="*60)
    
    # Only save if we have an assessment to save
    if assessment_type_to_save and assessment_report_to_save and patient_identifier:
        logger.info(f"Patient: {patient_identifier}")
        logger.info(f"Assessment Type: {assessment_type_to_save}")
        
        try:
            success = save_assessment_report(
                patient_identifier=patient_identifier,
                assessment_type=assessment_type_to_save,
                assessment_report=assessment_report_to_save,
                risk_levels=assessment_risk_levels,
            )
            
            if success:
                logger.info(f"✅ Report saved successfully for patient {patient_identifier}")
                state["persistence_status"] = "success"
            else:
                logger.error(f"❌ Failed to save report for patient {patient_identifier}")
                state["persistence_status"] = "failed"
        except Exception as e:
            logger.error(f"❌ Error during persistence: {str(e)}", exc_info=True)
            state["persistence_status"] = "error"
    else:
        logger.warning("⚠️ No assessment data to persist")
        state["persistence_status"] = "skipped"
    
    logger.info("="*60 + "\n")
    
    # ✅ Reset state after persistence completes
    reset_state(state)
    
    return state


def _enforce_concise_assessment_output(text: str) -> str:
    if not text:
        return text
    noisy_sections = [
        r"<sub><strong>Pipeline confidence</strong>[\s\S]*?</sub>",
        r"##?\s*Confidence Scores[\s\S]*?(?=\n## |\Z)",
        r"##?\s*Explainable AI Analysis[\s\S]*?(?=\n## |\Z)",
        r"##?\s*Key Clinical Insights[\s\S]*?(?=\n## |\Z)",
        r"##?\s*Interpretation Notes[\s\S]*?(?=\n## |\Z)",
        r"##?\s*Detected Structures[\s\S]*?(?=\n## |\Z)",
        r"##?\s*Patient Information[\s\S]*?(?=\n## |\Z)",
    ]
    out = text
    for p in noisy_sections:
        out = re.sub(p, "", out, flags=re.IGNORECASE)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out
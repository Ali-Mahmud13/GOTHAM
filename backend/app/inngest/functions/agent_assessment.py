"""Agent assessment Inngest function."""

import logging
import inngest
from typing import Dict, Any
from app.inngest.client import inngest_client
from app.services.agent_service import get_agent_service
from app.services.assessment_results import store_assessment_result

logger = logging.getLogger(__name__)


@inngest_client.create_function(
    fn_id="agent-assessment",
    trigger=inngest.TriggerEvent(event="agent/assessment.request"),
)
async def process_agent_assessment(ctx: inngest.Context) -> Dict[str, Any]:
    """
    Background job for processing agent-based risk assessment.
    
    Triggered by: agent/assessment.request event
    
    Event data:
        - assessment_id: Unique identifier for this assessment
        - message: User's message/query
        - session_id: Conversation session ID
        - patient_id: Optional patient identifier
    """
    assessment_id = ctx.event.data.get("assessment_id")
    message = ctx.event.data.get("message")
    session_id = ctx.event.data.get("session_id")
    patient_id = ctx.event.data.get("patient_id")
    
    logger.info(f"Starting assessment {assessment_id} for session {session_id}")
    
    # Single step: Run the full agent workflow
    result = await ctx.step.run(
        "run-agent-workflow",
        run_agent_workflow,
        message,
        session_id,
    )
    
    logger.info(f"Completed assessment {assessment_id}")
    
    # Store the result for polling
    assessment_result = {
        "assessment_id": assessment_id,
        "session_id": session_id,
        "patient_id": patient_id,
        "response": result.get("response"),
        "success": result.get("success"),
        "status": "completed"
    }
    
    store_assessment_result(assessment_id, assessment_result)
    
    return assessment_result


async def run_agent_workflow(message: str, session_id: str) -> Dict[str, Any]:
    """
    Execute the full agent workflow using the agent service.
    
    This runs all LangGraph nodes (check_clarity, load_data, 
    run_maternal, run_fetal, rag_retrieval, respond) in a single step.
    
    Args:
        message: User's message
        session_id: Session ID for conversation continuity
        
    Returns:
        Dict containing response and success status
    """
    agent_service = get_agent_service()
    result = await agent_service.process_message(message, session_id)
    return result

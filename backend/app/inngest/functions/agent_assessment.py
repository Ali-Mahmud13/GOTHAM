"""Agent assessment Inngest function."""

import logging
from datetime import timedelta
import inngest
from typing import Dict, Any
from app.inngest.client import inngest_client
from app.services.agent_service import get_agent_service
from app.services.assessment_results import (
    store_assessment_result,
    update_assessment_progress,
)
from app.services.assessment_persistence import save_assessment_report

logger = logging.getLogger(__name__)


@inngest_client.create_function(
    fn_id="agent-assessment",
    trigger=inngest.TriggerEvent(event="agent/assessment.request"),
    retries=1,
    timeouts=inngest.Timeouts(finish=timedelta(minutes=5)),
)
async def process_agent_assessment(ctx: inngest.Context) -> Dict[str, Any]:
    """
    Background job for processing agent-based risk assessment.

    Step 1 runs the full LangGraph agent with a progress callback that
    writes live status to the in-memory store (picked up by frontend polling).
    Step 2 persists the report to the database and stores the final result.
    """
    assessment_id = ctx.event.data.get("assessment_id")
    message = ctx.event.data.get("message")
    session_id = ctx.event.data.get("session_id")
    patient_id = ctx.event.data.get("patient_id")

    logger.info(f"Starting assessment {assessment_id} for session {session_id}")

    result = await ctx.step.run(
        "run-assessment",
        _run_assessment,
        assessment_id,
        message,
        session_id,
    )

    assessment_result = await ctx.step.run(
        "save-and-store",
        _save_and_store,
        assessment_id,
        session_id,
        patient_id,
        result,
    )

    return assessment_result


async def _run_assessment(
    assessment_id: str,
    message: str,
    session_id: str,
) -> Dict[str, Any]:
    """Run the LangGraph agent workflow with live progress reporting."""
    from app.agent.main_agent.state import set_progress_callback

    def _progress(step_number: int, label: str) -> None:
        update_assessment_progress(assessment_id, step_number, label)

    set_progress_callback(_progress)
    try:
        agent_service = get_agent_service()
        result = await agent_service.process_message(message, session_id)
    finally:
        set_progress_callback(None)
    return result


async def _save_and_store(
    assessment_id: str,
    session_id: str,
    patient_id: str | None,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """Persist the assessment report and store the final result for polling."""

    try:
        resolved_patient_id = patient_id or result.get("patient_id")
        assessment_report = result.get("assessment_report")
        assessment_type = result.get("assessment_type")
        assessment_risk_levels = result.get("assessment_risk_levels") or {}

        if (
            resolved_patient_id
            and assessment_report
            and assessment_type in {"maternal", "fetal", "both"}
        ):
            save_assessment_report(
                patient_identifier=resolved_patient_id,
                assessment_type=assessment_type,
                assessment_report=assessment_report,
                risk_levels=assessment_risk_levels,
            )

        logger.info(f"Completed assessment {assessment_id}")

        assessment_result: Dict[str, Any] = {
            "assessment_id": assessment_id,
            "session_id": session_id,
            "patient_id": resolved_patient_id,
            "response": assessment_report or result.get("response"),
            "success": result.get("success", True),
            "status": "completed",
            "assessment_type": assessment_type,
            "risk_levels": assessment_risk_levels,
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Assessment {assessment_id} failed: {error_msg}")

        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            user_msg = (
                "⚠️ **Rate Limit Reached**\n\n"
                "The AI service is temporarily unavailable due to rate limits. "
                "Please wait a few minutes and try again."
            )
        else:
            user_msg = f"❌ **Assessment Error**\n\n{error_msg}"

        assessment_result = {
            "assessment_id": assessment_id,
            "session_id": session_id,
            "patient_id": patient_id,
            "response": user_msg,
            "success": False,
            "status": "failed",
        }

    store_assessment_result(assessment_id, assessment_result)
    return assessment_result

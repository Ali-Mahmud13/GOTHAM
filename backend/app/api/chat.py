"""Chat API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import uuid4
from fastapi import Request
from app.core.rate_limit import limiter
from app.services.agent_service import get_agent_service, AgentService
from app.inngest.client import inngest_client
from app.services.assessment_results import (
    get_assessment_result,
    mark_assessment_processing,
    queue_inngest_event,
    get_fallback_queue_size
)
import inngest
import logging

from app.core.security import get_current_user_compat
from app.models.auth import AuthUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    session_id: str
    suggested_questions: list = []


class AssessmentRequest(BaseModel):
    """Request model for background assessment endpoint."""
    message: str
    session_id: Optional[str] = None
    patient_id: Optional[str] = None


class AssessmentResponse(BaseModel):
    """Response model for background assessment endpoint."""
    assessment_id: str
    session_id: str
    status: str
    message: str


@router.post("", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(request: Request, payload: ChatRequest, user: AuthUser = Depends(get_current_user_compat), agent_service: AgentService = Depends(get_agent_service)):
    """
    Process a chat message through the medical agent.
    
    Args:
        request: Request object for rate limiting
        payload: Chat request containing message and optional session_id
        
    Returns:
        ChatResponse with agent's response and session_id
    """
    try:
        logger.info(f"Received chat request (session: {payload.session_id})")
        
        # Process message with injected agent service
        # TODO: thread user_id into agent memory/persistence if needed.
        _ = user
        result = await agent_service.process_message(
            message=payload.message,
            session_id=payload.session_id
        )
        
        if not result.get("success", True):
            logger.error(f"Agent processing failed: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail="Failed to process message"
            )
        
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            suggested_questions=result.get("suggested_questions") or [],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@router.post("/assess", response_model=AssessmentResponse)
@limiter.limit("10/minute")
async def assess_risk(request: Request, payload: AssessmentRequest, user: AuthUser = Depends(get_current_user_compat)):
    """
    Trigger a background risk assessment.
    
    This endpoint immediately returns an assessment_id while the
    assessment runs in the background via Inngest.
    
    Args:
        request: Request object for rate limiting
        payload: Assessment request containing message, session_id, and patient_id
        
    Returns:
        AssessmentResponse with assessment_id and status
    """
    try:
        # Generate IDs
        assessment_id = str(uuid4())
        session_id = payload.session_id or str(uuid4())
        
        logger.info(
            f"Triggering background assessment {assessment_id} "
            f"for patient {payload.patient_id}"
        )
        
        _ = user
        # Mark as processing
        mark_assessment_processing(assessment_id)

        # Prepare event data
        event_data = {
            "assessment_id": assessment_id,
            "message": payload.message,
            "session_id": session_id,
            "patient_id": payload.patient_id,
        }

        # Trigger Inngest background job using official SDK
        try:
            await inngest_client.send(
                inngest.Event(
                    name="agent/assessment.request",
                    data=event_data,
                    id=assessment_id
                )
            )
            logger.info(f"Assessment {assessment_id} sent to Inngest")
        except (inngest.errors.SendEventsError, Exception) as e:
            logger.warning(
                f"Failed to send assessment {assessment_id} to Inngest: {str(e)}. "
                f"Queuing for fallback retry."
            )
            # Add to fallback queue for manual retry
            queue_inngest_event(event_data)
            logger.info(
                f"Assessment {assessment_id} queued to fallback queue. "
                f"Total queued: {get_fallback_queue_size()}"
            )

        return AssessmentResponse(
            assessment_id=assessment_id,
            session_id=session_id,
            status="processing",
            message="Risk assessment started. Check status using assessment_id."
        )
        
    except Exception as e:
        logger.error(f"Error triggering assessment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger assessment"
        )


@router.get("/assess/{assessment_id}")
async def get_assessment_status(assessment_id: str, user: AuthUser = Depends(get_current_user_compat)) -> Dict[str, Any]:
    """
    Get the status and result of a background assessment.
    
    Args:
        assessment_id: The ID of the assessment to check
        
    Returns:
        Status and result (if completed)
    """
    _ = user
    result = get_assessment_result(assessment_id)
    
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found"
        )
    
    return result

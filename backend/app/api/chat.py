"""Chat API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from app.services.agent_service import get_agent_service
from app.inngest.client import inngest_client
import inngest
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    session_id: str


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
async def chat(request: ChatRequest):
    """
    Process a chat message through the medical agent.
    
    Args:
        request: Chat request containing message and optional session_id
        
    Returns:
        ChatResponse with agent's response and session_id
    """
    try:
        logger.info(f"Received chat request (session: {request.session_id})")
        
        # Get agent service and process message
        agent_service = get_agent_service()
        result = await agent_service.process_message(
            message=request.message,
            session_id=request.session_id
        )
        
        if not result.get("success", True):
            logger.error(f"Agent processing failed: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail="Failed to process message"
            )
        
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"]
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
async def assess_risk(request: AssessmentRequest):
    """
    Trigger a background risk assessment.
    
    This endpoint immediately returns an assessment_id while the
    assessment runs in the background via Inngest.
    
    Args:
        request: Assessment request containing message, session_id, and patient_id
        
    Returns:
        AssessmentResponse with assessment_id and status
    """
    try:
        # Generate IDs
        assessment_id = str(uuid4())
        session_id = request.session_id or str(uuid4())
        
        logger.info(
            f"Triggering background assessment {assessment_id} "
            f"for patient {request.patient_id}"
        )
        
        # Trigger Inngest background job using official SDK
        await inngest_client.send(
            inngest.Event(
                name="agent/assessment.request",
                data={
                    "assessment_id": assessment_id,
                    "message": request.message,
                    "session_id": session_id,
                    "patient_id": request.patient_id,
                },
                id=assessment_id
            )
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

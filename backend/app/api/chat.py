"""Chat API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.agent_service import get_agent_service
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

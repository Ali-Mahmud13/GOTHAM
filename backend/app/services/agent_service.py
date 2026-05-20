"""Agent service - Handles agent graph invocation and session management."""

from typing import Dict, Any, Optional
from uuid import uuid4
from langchain_core.messages import HumanMessage, AIMessage
from app.core.sanitize import safe_for_prompt
from app.agent.main_agent.tools.helper.response_cache import get as cache_get, put as cache_put, invalidate_patient
import logging

logger = logging.getLogger(__name__)

# Assessment decision values that run the ML pipeline — never cache these.
_ASSESSMENT_TYPES = {"maternal", "fetal", "both"}


class AgentService:
    """Service class for managing the medical agent."""
    
    def __init__(self):
        """Initialize the agent service with the graph."""
        # Import here to avoid circular import
        from app.agent.main_agent.graph import create_graph
        self.graph = create_graph()
        logger.info("Agent service initialized with LangGraph")
    
    async def process_message(
        self, 
        message: str, 
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message through the agent.
        
        Args:
            message: User's message text
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Dict containing response and session_id
        """
        if not session_id:
            session_id = str(uuid4())
            logger.info(f"Generated new session ID: {session_id}")
        else:
            logger.info(f"Using existing session ID: {session_id}")
        
        config = {"configurable": {"thread_id": session_id}}
        
        safe_message = safe_for_prompt(message)
        state: Dict[str, Any] = {"messages": [HumanMessage(content=safe_message)]}

        # ── Cache check ───────────────────────────────────────────────
        # We need the patient_id to build the cache key. It lives in the
        # LangGraph thread state (persisted by MemorySaver). Fetch it cheaply
        # via get_state — no graph execution needed.
        current_patient_id: str | None = None
        try:
            thread_state = self.graph.get_state(config)
            current_patient_id = (thread_state.values or {}).get("current_patient_id")
        except Exception:
            pass  # No state yet for new sessions — that's fine

        if current_patient_id:
            cached = cache_get(current_patient_id, safe_message)
            if cached is not None:
                logger.info(f"Cache HIT for patient={current_patient_id} — skipping graph execution")
                return {
                    "response": cached,
                    "session_id": session_id,
                    "success": True,
                    "assessment_type": None,
                    "assessment_report": None,
                    "assessment_risk_levels": None,
                    "patient_id": current_patient_id,
                    "from_cache": True,
                }
        
        try:
            logger.info(f"Processing message: '{message[:100]}...'")
            
            result = await self.graph.ainvoke(state, config=config)
            
            # Extract assistant's response
            assistant_message = result["messages"][-1]
            
            if isinstance(assistant_message, AIMessage):
                response_text = assistant_message.content
            else:
                response_text = str(assistant_message.content)
            
            logger.info(f"Agent response generated (length: {len(response_text)})")

            assessment_type = result.get("assessment_type_to_save")
            assessment_report = result.get("assessment_report_to_save")
            assessment_risk_levels = result.get("assessment_risk_levels")
            resolved_patient_id = result.get("current_patient_id") or current_patient_id
            suggested_questions = result.get("suggested_questions") or []

            # ── Cache store / invalidation ────────────────────────────
            if resolved_patient_id:
                if assessment_type in _ASSESSMENT_TYPES:
                    # New assessment ran — patient's risk profile may have changed.
                    # Invalidate all cached responses for this patient.
                    invalidate_patient(resolved_patient_id)
                    logger.info(f"Cache invalidated for patient={resolved_patient_id} (new {assessment_type} assessment)")
                else:
                    # Conversational / RAG / follow-up response — safe to cache.
                    cache_put(resolved_patient_id, safe_message, response_text)

            return {
                "response": response_text,
                "session_id": session_id,
                "success": True,
                "assessment_type": assessment_type,
                "assessment_report": assessment_report,
                "assessment_risk_levels": assessment_risk_levels,
                "patient_id": resolved_patient_id,
                "suggested_questions": suggested_questions,
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "session_id": session_id,
                "success": False,
                "error": str(e)
            }
    
    def get_graph(self):
        """Get the underlying LangGraph instance."""
        return self.graph


_agent_service_instance: Optional[AgentService] = None

def get_agent_service() -> AgentService:
    """
    Get the agent service instance (Singleton).
    
    Returns:
        AgentService instance
    """
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance

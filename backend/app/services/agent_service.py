"""Agent service - Handles agent graph invocation and session management."""

from typing import Dict, Any, Optional
from uuid import uuid4
from langchain_core.messages import HumanMessage, AIMessage
import logging

logger = logging.getLogger(__name__)


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
        
        state: Dict[str, Any] = {"messages": [HumanMessage(content=message)]}
        
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
            current_patient_id = result.get("current_patient_id")
            
            return {
                "response": response_text,
                "session_id": session_id,
                "success": True,
                "assessment_type": assessment_type,
                "assessment_report": assessment_report,
                "assessment_risk_levels": assessment_risk_levels,
                "patient_id": current_patient_id,
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


# Singleton instance
_agent_service_instance = None


def get_agent_service() -> AgentService:
    """
    Get the singleton agent service instance.
    
    Returns:
        AgentService instance
    """
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance


"""LangGraph agent - Minimal setup."""

from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes.respond import generate_response


def create_medical_agent():
   
    workflow = StateGraph(AgentState)
    
    # Single node: respond
    workflow.add_node("respond", generate_response)
    
    # Simple flow
    workflow.set_entry_point("respond")
    workflow.add_edge("respond", END)
    
    return workflow.compile()


# Create the agent instance
medical_agent = create_medical_agent()

"""Inngest functions."""

from app.inngest.functions.agent_assessment import process_agent_assessment

# All registered Inngest functions
ALL_FUNCTIONS = [
    process_agent_assessment,  # Main agent workflow
]

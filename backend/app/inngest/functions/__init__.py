"""Inngest functions."""

from app.inngest.functions.agent_assessment import process_agent_assessment
from app.inngest.functions.risk_processing import risk_processing

# All registered Inngest functions
ALL_FUNCTIONS = [
    process_agent_assessment,  # Main agent workflow
    risk_processing,           # Risk processing example
]

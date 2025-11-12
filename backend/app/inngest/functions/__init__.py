"""Inngest functions."""

from app.inngest.functions.example import my_function
from app.inngest.functions.risk_processing import risk_processing
from app.inngest.functions.agent_assessment import process_agent_assessment
from app.inngest.functions.maternal_prediction import run_maternal_prediction
from app.inngest.functions.fetal_prediction import run_fetal_prediction
from app.inngest.functions.rag_retrieval import retrieve_medical_context

# Add all functions here
ALL_FUNCTIONS = [
    my_function,
    risk_processing,
    process_agent_assessment,
    run_maternal_prediction,
    run_fetal_prediction,
    retrieve_medical_context,
]

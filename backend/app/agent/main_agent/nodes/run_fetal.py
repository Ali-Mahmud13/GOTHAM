from ..state import AgentState
from ..tools.fetal_health_pipeline.temp_fetal import run_fetal_prediction

async def run_fetal_node(state: AgentState) -> AgentState:
    report = run_fetal_prediction()
    
    state["fetal_report"] = report
    
    return state
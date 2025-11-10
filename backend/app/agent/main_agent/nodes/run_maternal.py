from pathlib import Path
from ..state import AgentState
from ..tools.helper.clean_data import clean_data_for_model
from ..tools.maternal_health_pipeline.gdp.gdp_predictor_function import predict_gdp

async def run_maternal_node(state: AgentState) -> AgentState:
    # Get absolute path to contract file relative to this file
    current_file = Path(__file__)
    contract_path = current_file.parent.parent / "tools" / "maternal_health_pipeline" / "gdp" / "gdp_contract.yaml"
    
    cleaned_data = await clean_data_for_model(state["patient_data"], str(contract_path))

    print("\n--- CLEANED DATA FOR MODEL ---")
    for key, value in cleaned_data.items():
        print(f"{key}: {value}")
    print("------------------------------\n")
    
    report = await predict_gdp(**cleaned_data)

    print("\n--- MATERNAL HEALTH REPORT ---")
    print(report)
    print("------------------------------\n")

    state["maternal_report"] = report
    
    return state
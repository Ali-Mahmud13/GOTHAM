import asyncio
from agent.tools.helper.clean_data import clean_data_for_model


async def main():
    # fake patient data (you can change or load real one)
    patient_data = {
        "age": 25,
        "bmi": 22.5,
        "dia_bp": 70,
        "hdl": 55,
        "hemoglobin": 13.2,
        "no_of_pregnancy": 1,
        "ogtt": 90,
        "sys_bp": 110,
        "gestation_in_previous_pregnancy": 0,
        "family_history": 1,
        "unexplained_prenatal_loss": 0,
        "large_child_or_birth_default": 0,
        "pcos": 0,
        "sedentary_lifestyle": 1,
        "prediabetes": 0,
        "model_path": "GDP_model.pkl"
    }

    cleaned = await clean_data_for_model(
    patient_data,
    "./agent/tools/maternal_health_pipeline/gdp/gdp_contract.yaml"
)

    for k, v in cleaned.items():
        print(f"{k}: {v}")

asyncio.run(main())

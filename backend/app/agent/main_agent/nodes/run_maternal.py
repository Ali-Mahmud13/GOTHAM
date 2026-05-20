from pathlib import Path
from ..state import AgentState, report_progress
from ..tools.helper.clean_data import clean_data_for_model
from ..tools.maternal_health_pipeline.gdp.gdp_predictor_function import predict_gdp
from ..tools.maternal_health_pipeline.anemia.anemia import generate_anemia_xai_report as predict_anemia
from ..tools.helper.benchmark import record, summary
import inspect
import asyncio
import time

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def _run_single_maternal(model_config: dict, patient_data: dict) -> str:
    """
    Run one maternal model and return a formatted report string.
    Designed to be called concurrently via asyncio.gather().
    Returns the formatted report (or an error string) — never raises.
    """
    model_name = model_config["name"]
    logger.info(f"[PARALLEL] Starting: {model_name}")

    try:
        # Clean data according to model's contract
        cleaned_data = await clean_data_for_model(
            patient_data,
            str(model_config["contract_path"])
        )

        logger.info(f"Cleaned data for {model_name}:")
        for key, value in cleaned_data.items():
            logger.info(f"  {key}: {value}")

        # Check if all required data is available
        if not cleaned_data or any(v is None for v in cleaned_data.values()):
            missing_fields = [k for k, v in cleaned_data.items() if v is None]
            error_msg = f"⚠️ **Incomplete Data**\nMissing fields: {', '.join(missing_fields)}"
            logger.warning(f"Skipping {model_name} - missing data: {missing_fields}")
            return f"## {model_name}\n\n{error_msg}\n"

        # Run the prediction — handle both async and sync functions
        logger.info(f"Calling predictor with args: {cleaned_data}")
        predictor_func = model_config["predictor_function"]
        if inspect.iscoroutinefunction(predictor_func):
            report = await predictor_func(**cleaned_data)
        else:
            report = predictor_func(**cleaned_data)

        logger.info(f"✓ {model_name} completed successfully")
        return f"## {model_name}\n\n{report}\n"

    except FileNotFoundError as e:
        logger.error(f"Contract not found for {model_name}: {e}")
        return f"## {model_name}\n\n❌ **Model Error**\nContract file not found: {e}\n"

    except KeyError as e:
        logger.error(f"Missing field for {model_name}: {e}")
        return f"## {model_name}\n\n⚠️ **Data Error**\nRequired field missing from patient data: {e}\n"

    except Exception as e:
        logger.error(f"Error running {model_name}: {e}", exc_info=True)
        return f"## {model_name}\n\n❌ **Prediction Error**\n{str(e)}\n"


async def run_maternal_node(state: AgentState) -> AgentState:
    """
    Run all maternal health models in parallel and concatenate results.
    GDM and Anemia now run concurrently via asyncio.gather().
    """
    report_progress(3, "Running maternal health models")
    _node_start = time.perf_counter()
    logger.info("=" * 60)
    logger.info("RUN MATERNAL NODE - Starting all models (PARALLEL)")
    logger.info("=" * 60)

    current_file = Path(__file__)
    tools_path = current_file.parent.parent / "tools" / "maternal_health_pipeline"

    models_config = [
        {
            "name": "Gestational Diabetes Prediction",
            "contract_path": tools_path / "gdp" / "gdp_contract.yaml",
            "predictor_function": predict_gdp
        },
        {
            "name": "Maternal Anemia",
            "contract_path": tools_path / "anemia" / "anemia_contract.yml",
            "predictor_function": predict_anemia
        },
    ]

    patient_data = state["patient_data"]

    # ── Run all models concurrently ───────────────────────────
    # Order of results matches order of models_config (gather preserves order).
    maternal_reports: list[str] = await asyncio.gather(
        *[_run_single_maternal(cfg, patient_data) for cfg in models_config]
    )

    final_report = "\n".join(maternal_reports)

    logger.info("\n" + "=" * 60)
    logger.info("MATERNAL HEALTH ASSESSMENT - COMPLETE")
    logger.info("=" * 60)
    logger.info(f"\n{final_report}")
    logger.info("=" * 60 + "\n")

    record("Node Total: run_maternal (parallel)", time.perf_counter() - _node_start)
    logger.info(summary())

    state["maternal_report"] = final_report

    return state
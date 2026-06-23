from pathlib import Path
import asyncio
import inspect
import logging
import time

from ..model_results import attach_input_metadata, failed_result, incomplete_result
from ..state import AgentState, report_progress
from ..tools.helper.benchmark import record, summary
from ..tools.helper.clean_data import clean_data_for_model
from ..tools.maternal_health_pipeline.anemia.anemia import (
    generate_anemia_xai_report as predict_anemia,
)
from ..tools.maternal_health_pipeline.gdp.gdp_predictor_function import predict_gdp
from ..tools.maternal_health_pipeline.preeclampsia_predictor import (
    predict_preeclampsia,
)

logger = logging.getLogger(__name__)


async def _run_single_maternal(
    model_config: dict,
    patient_data: dict,
) -> dict:
    """Run one maternal model and always return a structured result."""
    model_key = model_config["key"]
    model_name = model_config["name"]
    logger.info("[PARALLEL] Starting: %s", model_name)

    try:
        cleaned_data = await clean_data_for_model(
            patient_data,
            str(model_config["contract_path"]),
        )
        if not cleaned_data or any(value is None for value in cleaned_data.values()):
            result = incomplete_result(
                model_key,
                model_name,
                cleaned_data,
                patient_data,
            )
            logger.warning(
                "Skipping %s - missing data: %s",
                model_name,
                result["missing_fields"],
            )
            return result

        predictor = model_config["predictor_function"]
        if inspect.iscoroutinefunction(predictor):
            result = await predictor(**cleaned_data)
        else:
            result = await asyncio.to_thread(predictor, **cleaned_data)

        result["model"] = model_key
        result["report"] = f"## {model_name}\n\n{result['report']}\n"
        logger.info("%s completed successfully", model_name)
        return attach_input_metadata(result, cleaned_data, patient_data)
    except FileNotFoundError as exc:
        logger.error("Contract not found for %s: %s", model_name, exc)
        return failed_result(model_key, model_name, f"Contract file not found: {exc}")
    except KeyError as exc:
        logger.error("Missing field for %s: %s", model_name, exc)
        return failed_result(model_key, model_name, f"Required field missing: {exc}")
    except Exception as exc:
        logger.error("Error running %s: %s", model_name, exc, exc_info=True)
        return failed_result(model_key, model_name, str(exc))


async def run_maternal_node(state: AgentState) -> AgentState:
    """Run all maternal models concurrently and retain structured results."""
    report_progress(3, "Running maternal health models")
    node_start = time.perf_counter()
    tools_path = (
        Path(__file__).parent.parent / "tools" / "maternal_health_pipeline"
    )

    models_config = [
        {
            "key": "gdm",
            "name": "Gestational Diabetes Prediction",
            "contract_path": tools_path / "gdp" / "gdp_contract.yaml",
            "predictor_function": predict_gdp,
        },
        {
            "key": "anemia",
            "name": "Maternal Anemia",
            "contract_path": tools_path / "anemia" / "anemia_contract.yml",
            "predictor_function": predict_anemia,
        },
        {
            "key": "preeclampsia",
            "name": "Preeclampsia Risk Assessment",
            "contract_path": tools_path / "maternal_health" / "mm-contract.yml",
            "predictor_function": predict_preeclampsia,
        },
    ]

    patient_data = state["patient_data"]
    results: list[dict] = await asyncio.gather(
        *[_run_single_maternal(config, patient_data) for config in models_config]
    )

    state["maternal_report"] = "\n".join(result["report"] for result in results)
    state["model_results"] = {
        **(state.get("model_results") or {}),
        **{result["model"]: result for result in results},
    }

    record("Node Total: run_maternal (parallel)", time.perf_counter() - node_start)
    logger.info(summary())
    return state

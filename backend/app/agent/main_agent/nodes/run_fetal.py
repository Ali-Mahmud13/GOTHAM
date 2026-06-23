from pathlib import Path
import asyncio
import logging
import re
import time

from ..model_results import attach_input_metadata, failed_result, incomplete_result
from ..state import AgentState, report_progress
from ..tools.fetal_health_pipeline.FHP.FHP_predictor import predict_fetal_health
from ..tools.fetal_health_pipeline.ultrasound.us import predict_ultrasound
from ..tools.helper.benchmark import record, summary
from ..tools.helper.clean_data import clean_data_for_model

logger = logging.getLogger(__name__)


async def _run_fhp(patient_data: dict, contract_path: str) -> dict:
    model_name = "Fetal Health Assessment"
    try:
        cleaned_data = await clean_data_for_model(patient_data, contract_path)
        if not cleaned_data or any(value is None for value in cleaned_data.values()):
            return incomplete_result("fetal", model_name, cleaned_data, patient_data)

        try:
            result = await asyncio.wait_for(
                predict_fetal_health(**cleaned_data),
                timeout=30,
            )
        except asyncio.TimeoutError:
            return failed_result("fetal", model_name, "Prediction timed out.")

        result["model"] = "fetal"
        result["report"] = f"## {model_name}\n\n{result['report']}\n"
        return attach_input_metadata(result, cleaned_data, patient_data)
    except FileNotFoundError as exc:
        return failed_result("fetal", model_name, f"Contract file not found: {exc}")
    except KeyError as exc:
        return failed_result("fetal", model_name, f"Required field missing: {exc}")
    except Exception as exc:
        logger.error("Error running %s: %s", model_name, exc, exc_info=True)
        return failed_result("fetal", model_name, str(exc))


async def _run_ultrasound(
    patient_data: dict,
    contract_path: str,
) -> tuple[str, str | None, str | None]:
    model_name = "Fetal Ultrasound Brain Structure Detection"
    try:
        cleaned_data = await clean_data_for_model(patient_data, contract_path)
        image_url = cleaned_data.get("latest_ultrasound_image_url")
        if not image_url:
            return (
                f"## {model_name}\n\n"
                "**Ultrasound Image Not Available**\n"
                "No ultrasound image found for this patient. Analysis skipped.\n",
                None,
                None,
            )

        try:
            report = await asyncio.wait_for(predict_ultrasound(image_url), timeout=30)
        except asyncio.TimeoutError:
            return (
                f"## {model_name}\n\n**Timeout Error**\nAnalysis timed out.\n",
                None,
                None,
            )

        annotated_url = None
        if isinstance(report, str):
            matches = re.findall(r"!\[.*?\]\((.*?)\)", report)
            if matches:
                annotated_url = matches[-1]
        return f"## {model_name}\n\n{report}\n", report, annotated_url
    except Exception as exc:
        logger.error("Ultrasound analysis failed: %s", exc, exc_info=True)
        return (
            f"## {model_name}\n\n**Prediction Error**\n{exc}\n",
            None,
            None,
        )


async def run_fetal_node(state: AgentState) -> AgentState:
    """Run CTG and ultrasound analysis concurrently."""
    report_progress(4, "Running fetal health models")
    node_start = time.perf_counter()
    tools_path = Path(__file__).parent.parent / "tools" / "fetal_health_pipeline"
    patient_data = state["patient_data"]

    fhp_result, ultrasound_result = await asyncio.gather(
        _run_fhp(patient_data, str(tools_path / "FHP" / "FHP_contract.yaml")),
        _run_ultrasound(
            patient_data,
            str(tools_path / "ultrasound" / "uscontract.yaml"),
        ),
    )
    ultrasound_formatted, ultrasound_report, annotated_url = ultrasound_result

    if annotated_url:
        state["annotated_ultrasound_image_url"] = annotated_url
    state["fetal_report"] = "\n".join(
        [fhp_result["report"], ultrasound_formatted]
    )
    state["ultrasound_report"] = ultrasound_report
    state["model_results"] = {
        **(state.get("model_results") or {}),
        "fetal": fhp_result,
    }

    record("Node Total: run_fetal (parallel)", time.perf_counter() - node_start)
    logger.info(summary())
    return state

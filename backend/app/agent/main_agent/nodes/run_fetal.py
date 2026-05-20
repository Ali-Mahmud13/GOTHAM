from pathlib import Path
from ..state import AgentState, report_progress
from ..tools.helper.clean_data import clean_data_for_model
from ..tools.fetal_health_pipeline.FHP.FHP_predictor import predict_fetal_health
from ..tools.fetal_health_pipeline.ultrasound.us import predict_ultrasound
from ..tools.helper.benchmark import record, summary
import logging
import asyncio
import re
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def _run_fhp(patient_data: dict, contract_path: str) -> str:
    """
    Run the FHP (Fetal Health Prediction) data-based model.
    Returns a formatted report string. Never raises.
    """
    model_name = "Fetal Health Assessment"
    logger.info(f"[PARALLEL] Starting: {model_name}")

    try:
        cleaned_data = await clean_data_for_model(patient_data, contract_path)

        logger.info(f"Cleaned data for {model_name}:")
        for key, value in cleaned_data.items():
            logger.info(f"  {key}: {value}")

        if not cleaned_data or any(v is None for v in cleaned_data.values()):
            missing_fields = [k for k, v in cleaned_data.items() if v is None]
            error_msg = f"⚠️ **Incomplete Data**\nMissing fields: {', '.join(missing_fields)}"
            logger.warning(f"Skipping {model_name} - missing data: {missing_fields}")
            return f"## {model_name}\n\n{error_msg}\n"

        logger.info(f"DEBUG: Calling predictor for {model_name}")
        try:
            report = await asyncio.wait_for(
                predict_fetal_health(**cleaned_data),
                timeout=30
            )
            logger.info(f"✓ {model_name} completed successfully")
            return f"## {model_name}\n\n{report}\n"
        except asyncio.TimeoutError:
            logger.error(f"TIMEOUT: {model_name} exceeded 30s")
            return f"## {model_name}\n\n❌ **Timeout Error**\nPrediction took too long and was cancelled.\n"

    except FileNotFoundError as e:
        logger.error(f"Contract not found for {model_name}: {e}")
        return f"## {model_name}\n\n❌ **Model Error**\nContract file not found: {e}\n"
    except KeyError as e:
        logger.error(f"Missing field for {model_name}: {e}")
        return f"## {model_name}\n\n⚠️ **Data Error**\nRequired field missing: {e}\n"
    except Exception as e:
        logger.error(f"Error running {model_name}: {e}", exc_info=True)
        return f"## {model_name}\n\n❌ **Prediction Error**\n{str(e)}\n"


async def _run_ultrasound(patient_data: dict, contract_path: str) -> tuple[str, str | None, str | None]:
    """
    Run the ultrasound image-based model.
    Returns (formatted_report, ultrasound_report_raw, annotated_image_url).
    The annotated URL is returned rather than mutating state directly,
    so it can be safely applied after asyncio.gather() completes.
    Never raises.
    """
    model_name = "Fetal Ultrasound Brain Structure Detection"
    logger.info(f"[PARALLEL] Starting: {model_name}")

    try:
        cleaned_data = await clean_data_for_model(patient_data, contract_path)
        latest_ultrasound_image_url = cleaned_data.get("latest_ultrasound_image_url")
        logger.info(f"DEBUG: Extracted image URL from contract: {repr(latest_ultrasound_image_url)}")

        if not latest_ultrasound_image_url:
            warning_msg = "⚠️ **Ultrasound Image Not Available**\nNo ultrasound image found for this patient. Ultrasound analysis skipped."
            logger.info(f"Skipped {model_name} - no ultrasound image")
            return f"## {model_name}\n\n{warning_msg}\n", None, None

        logger.info(f"DEBUG: Calling predict_ultrasound with image: {latest_ultrasound_image_url}")
        try:
            report = await asyncio.wait_for(
                predict_ultrasound(latest_ultrasound_image_url),
                timeout=30
            )
            # Extract annotated image URL from report markdown — returned to caller
            annotated_url = None
            if isinstance(report, str):
                matches = re.findall(r"!\[.*?\]\((.*?)\)", report)
                if matches:
                    annotated_url = matches[-1]

            logger.info(f"✓ {model_name} completed successfully")
            return f"## {model_name}\n\n{report}\n", report, annotated_url

        except asyncio.TimeoutError:
            logger.error(f"TIMEOUT: {model_name} exceeded 30s")
            return f"## {model_name}\n\n❌ **Timeout Error**\nUltrasound analysis took too long and was cancelled.\n", None, None

    except FileNotFoundError as e:
        logger.error(f"Contract not found for {model_name}: {e}")
        return f"## {model_name}\n\n❌ **Model Error**\nContract file not found: {e}\n", None, None
    except KeyError as e:
        logger.error(f"Missing field for {model_name}: {e}")
        return f"## {model_name}\n\n⚠️ **Data Error**\nRequired field missing: {e}\n", None, None
    except Exception as e:
        logger.error(f"Error running {model_name}: {e}", exc_info=True)
        return f"## {model_name}\n\n❌ **Prediction Error**\n{str(e)}\n", None, None


async def run_fetal_node(state: AgentState) -> AgentState:
    """
    Run all fetal health models in parallel and concatenate results.
    FHP and Ultrasound now run concurrently via asyncio.gather().
    """
    report_progress(4, "Running fetal health models")
    _node_start = time.perf_counter()

    logger.info("=" * 60)
    logger.info("RUN FETAL NODE - Starting all models (PARALLEL)")
    logger.info("=" * 60)

    current_file = Path(__file__)
    tools_path = current_file.parent.parent / "tools" / "fetal_health_pipeline"
    patient_data = state["patient_data"]

    fhp_contract = str(tools_path / "FHP" / "FHP_contract.yaml")
    us_contract = str(tools_path / "ultrasound" / "uscontract.yaml")

    # ── Run FHP and Ultrasound concurrently ──────────────────
    fhp_report, us_result = await asyncio.gather(
        _run_fhp(patient_data, fhp_contract),
        _run_ultrasound(patient_data, us_contract),
    )

    # _run_ultrasound returns (formatted_report, raw_report, annotated_url)
    us_formatted, ultrasound_report, annotated_url = us_result

    fetal_reports = [fhp_report, us_formatted]
    final_report = "\n".join(fetal_reports)

    # Apply the annotated URL to state — safe to do here after gather completes
    if annotated_url:
        state["annotated_ultrasound_image_url"] = annotated_url

    logger.info("\n" + "=" * 60)
    logger.info("FETAL HEALTH ASSESSMENT - COMPLETE")
    logger.info("=" * 60)
    logger.info(f"\n{final_report}")
    logger.info("=" * 60 + "\n")

    record("Node Total: run_fetal (parallel)", time.perf_counter() - _node_start)
    logger.info(summary())

    state["fetal_report"] = final_report
    # ✅ Store ultrasound report separately for respond_node to access
    state["ultrasound_report"] = ultrasound_report

    return state
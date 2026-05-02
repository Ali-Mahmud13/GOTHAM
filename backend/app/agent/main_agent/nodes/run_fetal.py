from pathlib import Path
from ..state import AgentState, report_progress
from ..tools.helper.clean_data import clean_data_for_model
from ..tools.fetal_health_pipeline.FHP.FHP_predictor import predict_fetal_health
from ..tools.fetal_health_pipeline.ultrasound.us import predict_ultrasound
import logging
import asyncio
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_fetal_node(state: AgentState) -> AgentState:
    """
    Run all fetal health models and concatenate results
    """

    report_progress(4, "Running fetal health models")

    logger.info("="*60)
    logger.info("RUN FETAL NODE - Starting all models")
    logger.info("="*60)
    
    current_file = Path(__file__)
    tools_path = current_file.parent.parent / "tools" / "fetal_health_pipeline"
    
    fetal_reports = []
    patient_data = state["patient_data"]
    
    models_config = [
        {
            "name": "Fetal Health Assessment",
            "contract_path": tools_path / "FHP" / "FHP_contract.yaml",
            "predictor_function": predict_fetal_health,
            "requires_image": False
        },
        {
            "name": "Fetal Ultrasound Brain Structure Detection",
            "contract_path": tools_path / "ultrasound" / "uscontract.yaml",
            "predictor_function": predict_ultrasound,
            "requires_image": True
        },
    ]
    
    ultrasound_report = None  # ✅ Track ultrasound report separately
    
    # Run each model
    for model_config in models_config:
        model_name = model_config["name"]
        logger.info(f"\nProcessing model: {model_name}")
        
        try:
            # ✅ SPECIAL HANDLING FOR IMAGE-BASED MODELS
            if model_config.get("requires_image"):
                logger.info(f"DEBUG: This is an image-based model, using contract to get image URL")
                
                # ✅ Use clean_data_for_model to extract latest_ultrasound_image_url from contract
                cleaned_data = await clean_data_for_model(
                    patient_data, 
                    str(model_config["contract_path"])
                )
                
                latest_ultrasound_image_url = cleaned_data.get("latest_ultrasound_image_url")
                logger.info(f"DEBUG: Extracted image URL from contract: {repr(latest_ultrasound_image_url)}")
                
                if not latest_ultrasound_image_url:
                    warning_msg = "⚠️ **Ultrasound Image Not Available**\nNo ultrasound image found for this patient. Ultrasound analysis skipped."
                    fetal_reports.append(f"## {model_name}\n\n{warning_msg}\n")
                    logger.info(f"Skipped {model_name} - no ultrasound image")
                    continue
                
                logger.info(f"DEBUG: Calling predict_ultrasound with image: {latest_ultrasound_image_url}")
                try:
                    report = await asyncio.wait_for(
                        model_config["predictor_function"](latest_ultrasound_image_url),
                        timeout=30
                    )
                    ultrasound_report = report  # ✅ Store separately
                    if isinstance(report, str):
                        matches = re.findall(r"!\[.*?\]\((.*?)\)", report)
                        if matches:
                            state["annotated_ultrasound_image_url"] = matches[-1]
                    formatted_report = f"## {model_name}\n\n{report}\n"
                    fetal_reports.append(formatted_report)
                    logger.info(f"✓ {model_name} completed successfully")
                except asyncio.TimeoutError:
                    logger.error(f"TIMEOUT: {model_name} exceeded 30s")
                    fetal_reports.append(f"## {model_name}\n\n❌ **Timeout Error**\nUltrasound analysis took too long and was cancelled.\n")
                
                continue
            
            # ✅ NORMAL FLOW FOR DATA-BASED MODELS
            logger.info(f"DEBUG: Processing data-based model: {model_name}")
            
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
                fetal_reports.append(f"## {model_name}\n\n{error_msg}\n")
                logger.warning(f"Skipping {model_name} - missing data: {missing_fields}")
                continue
            
            logger.info(f"DEBUG: Calling predictor for {model_name}")
            try:
                report = await asyncio.wait_for(
                    model_config["predictor_function"](**cleaned_data),
                    timeout=30
                )
                logger.info(f"DEBUG: {model_name} predictor returned")
            except asyncio.TimeoutError:
                logger.error(f"TIMEOUT: {model_name} exceeded 30s")
                fetal_reports.append(f"## {model_name}\n\n❌ **Timeout Error**\nPrediction took too long and was cancelled.\n")
                continue
            
            # Format the report
            formatted_report = f"## {model_name}\n\n{report}\n"
            fetal_reports.append(formatted_report)
            
            logger.info(f"✓ {model_name} completed successfully")
            
        except FileNotFoundError as e:
            error_msg = f"❌ **Model Error**\nContract file not found: {e}"
            fetal_reports.append(f"## {model_name}\n\n{error_msg}\n")
            logger.error(f"Contract not found for {model_name}: {e}")
            
        except KeyError as e:
            error_msg = f"⚠️ **Data Error**\nRequired field missing from patient data: {e}"
            fetal_reports.append(f"## {model_name}\n\n{error_msg}\n")
            logger.error(f"Missing field for {model_name}: {e}")
            
        except Exception as e:
            error_msg = f"❌ **Prediction Error**\n{str(e)}"
            fetal_reports.append(f"## {model_name}\n\n{error_msg}\n")
            logger.error(f"Error running {model_name}: {e}", exc_info=True)
    
    # Concatenate all reports
    final_report = "\n".join(fetal_reports)
    
    logger.info("\n" + "="*60)
    logger.info("FETAL HEALTH ASSESSMENT - COMPLETE")
    logger.info("="*60)
    logger.info(f"\n{final_report}")
    logger.info("="*60 + "\n")
    
    state["fetal_report"] = final_report
    # ✅ Store ultrasound report separately for respond_node to access
    state["ultrasound_report"] = ultrasound_report
    
    return state
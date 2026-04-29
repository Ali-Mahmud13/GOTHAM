from pathlib import Path
from ..state import AgentState
from ..tools.helper.clean_data import clean_data_for_model
from ..tools.fetal_health_pipeline.FHP.FHP_predictor import predict_fetal_health
from ..tools.fetal_health_pipeline.ultrasound.us import predict_ultrasound
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_fetal_node(state: AgentState) -> AgentState:
    """
    Run all fetal health models and concatenate results
    """
    logger.info("="*60)
    logger.info("RUN FETAL NODE - Starting all models")
    logger.info("="*60)
    
    current_file = Path(__file__)
    tools_path = current_file.parent.parent / "tools" / "fetal_health_pipeline"
    
    # Define models configuration
    models_config = [
        {
            "name": "Fetal Health Assessment",
            "contract_path": tools_path / "FHP" / "FHP_contract.yaml",
            "predictor_function": predict_fetal_health
        },
        {
            "name": "Fetal Ultrasound Brain Structure Detection",
            "contract_path": tools_path / "ultrasound" / "uscontract.yaml",
            "predictor_function": predict_ultrasound
        },
        # Add more fetal health models here in the future:
        # {
        #     "name": "Another Fetal Model",
        #     "contract_path": tools_path / "other_model" / "contract.yaml",
        #     "predictor_function": predict_other_fetal_model
        # }
    ]
    
    fetal_reports = []
    patient_data = state["patient_data"]
    
    # Run each model
    for model_config in models_config:
        model_name = model_config["name"]
        logger.info(f"\nProcessing model: {model_name}")
        
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
                fetal_reports.append(f"## {model_name}\n\n{error_msg}\n")
                logger.warning(f"Skipping {model_name} - missing data: {missing_fields}")
                continue
            
            # Run the prediction
            report = await model_config["predictor_function"](**cleaned_data)
            
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
    
    return state
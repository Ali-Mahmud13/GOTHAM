from pathlib import Path
from ..state import AgentState, report_progress
from ..tools.helper.clean_data import clean_data_for_model
from ..tools.maternal_health_pipeline.gdp.gdp_predictor_function import predict_gdp
from ..tools.maternal_health_pipeline.anemia.anemia import generate_anemia_xai_report as predict_anemia
import inspect

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_maternal_node(state: AgentState) -> AgentState:
    """
    Run all maternal health models and concatenate results
    """
    report_progress(3, "Running maternal health models")
    logger.info("="*60)
    logger.info("RUN MATERNAL NODE - Starting all models")
    logger.info("="*60)
    
    current_file = Path(__file__)
    tools_path = current_file.parent.parent / "tools" / "maternal_health_pipeline"
    
    # Define models configuration
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
        # {
        #     "name": "Maternal Anemia Detection",
        #     "contract_path": tools_path / "anemia" / "anemia_contract.yaml",
        #     "predictor_function": predict_anemia
        # }
    ]
    
    maternal_reports = []
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
                maternal_reports.append(f"## {model_name}\n\n{error_msg}\n")
                logger.warning(f"Skipping {model_name} - missing data: {missing_fields}")
                continue
            
            # Run the prediction - handle both async and sync functions
            logger.info(f"Calling predictor with args: {cleaned_data}")
            predictor_func = model_config["predictor_function"]
            if inspect.iscoroutinefunction(predictor_func):
                report = await predictor_func(**cleaned_data)
            else:
                report = predictor_func(**cleaned_data)
            
            # Format the report
            formatted_report = f"## {model_name}\n\n{report}\n"
            maternal_reports.append(formatted_report)
            
            logger.info(f"✓ {model_name} completed successfully")
            
        except FileNotFoundError as e:
            error_msg = f"❌ **Model Error**\nContract file not found: {e}"
            maternal_reports.append(f"## {model_name}\n\n{error_msg}\n")
            logger.error(f"Contract not found for {model_name}: {e}")
            
        except KeyError as e:
            error_msg = f"⚠️ **Data Error**\nRequired field missing from patient data: {e}"
            maternal_reports.append(f"## {model_name}\n\n{error_msg}\n")
            logger.error(f"Missing field for {model_name}: {e}")
            
        except Exception as e:
            error_msg = f"❌ **Prediction Error**\n{str(e)}"
            maternal_reports.append(f"## {model_name}\n\n{error_msg}\n")
            logger.error(f"Error running {model_name}: {e}", exc_info=True)
    
    # Concatenate all reports
    final_report = "\n".join(maternal_reports)
    
    logger.info("\n" + "="*60)
    logger.info("MATERNAL HEALTH ASSESSMENT - COMPLETE")
    logger.info("="*60)
    logger.info(f"\n{final_report}")
    logger.info("="*60 + "\n")
    
    state["maternal_report"] = final_report
    
    return state
"""Maternal health prediction Inngest function."""

import logging
import inngest
from typing import Dict, Any
from app.inngest.client import inngest_client

logger = logging.getLogger(__name__)


@inngest_client.create_function(
    fn_id="maternal-prediction",
    trigger=inngest.TriggerEvent(event="prediction/maternal.run"),
)
async def run_maternal_prediction(ctx: inngest.Context) -> Dict[str, Any]:
    """
    Background job for running maternal health predictions.
    
    Triggered by: prediction/maternal.run event
    
    Event data:
        - assessment_id: Unique identifier for this assessment
        - patient_data: Patient data for prediction
        - models: List of models to run (e.g., ['gdm', 'preeclampsia'])
    """
    assessment_id = ctx.event.data.get("assessment_id")
    patient_data = ctx.event.data.get("patient_data")
    models = ctx.event.data.get("models", [])
    
    logger.info(f"Running maternal predictions for assessment {assessment_id}, models: {models}")
    
    # Step 1: Run maternal health predictions
    results = await ctx.step.run(
        "run-maternal-models",
        execute_maternal_models,
        patient_data,
        models,
    )
    
    logger.info(f"Completed maternal predictions for assessment {assessment_id}")
    
    return {
        "assessment_id": assessment_id,
        "type": "maternal",
        "results": results,
        "status": "completed"
    }


async def execute_maternal_models(
    patient_data: Dict[str, Any],
    models: list,
) -> Dict[str, Any]:
    """
    Execute maternal health prediction models.
    
    Args:
        patient_data: Patient data dictionary
        models: List of model names to run
        
    Returns:
        Dict containing prediction results
    """
    # Import here to avoid circular imports
    from app.agent.main_agent.tools.maternal_health_pipeline.gdp.gdp_predictor_function import predict_gdp
    
    results = {}
    
    for model in models:
        try:
            if model == "gdp" or model == "gestational_diabetes":
                # Run GDP (Gestational Diabetes) prediction
                prediction = predict_gdp(patient_data)
                results["gestational_diabetes"] = prediction
            else:
                logger.warning(f"Unknown maternal model: {model}")
                
        except Exception as e:
            logger.error(f"Error running maternal model {model}: {str(e)}", exc_info=True)
            results[model] = {"error": str(e)}
    
    return results


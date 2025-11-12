"""Fetal health prediction Inngest function."""

import logging
import inngest
from typing import Dict, Any
from app.inngest.client import inngest_client

logger = logging.getLogger(__name__)


@inngest_client.create_function(
    fn_id="fetal-prediction",
    trigger=inngest.TriggerEvent(event="prediction/fetal.run"),
)
async def run_fetal_prediction(ctx: inngest.Context) -> Dict[str, Any]:
    """
    Background job for running fetal health predictions.
    
    Triggered by: prediction/fetal.run event
    
    Event data:
        - assessment_id: Unique identifier for this assessment
        - patient_data: Patient data for prediction
        - models: List of models to run
    """
    assessment_id = ctx.event.data.get("assessment_id")
    patient_data = ctx.event.data.get("patient_data")
    models = ctx.event.data.get("models", [])
    
    logger.info(f"Running fetal predictions for assessment {assessment_id}, models: {models}")
    
    # Step 1: Run fetal health predictions
    results = await ctx.step.run(
        "run-fetal-models",
        execute_fetal_models,
        patient_data,
        models,
    )
    
    logger.info(f"Completed fetal predictions for assessment {assessment_id}")
    
    return {
        "assessment_id": assessment_id,
        "type": "fetal",
        "results": results,
        "status": "completed"
    }


async def execute_fetal_models(
    patient_data: Dict[str, Any],
    models: list,
) -> Dict[str, Any]:
    """
    Execute fetal health prediction models.
    
    Args:
        patient_data: Patient data dictionary
        models: List of model names to run
        
    Returns:
        Dict containing prediction results
    """
    # Import here to avoid circular imports
    from app.agent.main_agent.tools.fetal_health_pipeline.temp_fetal import predict_fetal_health
    
    results = {}
    
    for model in models:
        try:
            if model == "fetal_health" or model == "fetal":
                # Run fetal health prediction
                prediction = predict_fetal_health(patient_data)
                results["fetal_health"] = prediction
            else:
                logger.warning(f"Unknown fetal model: {model}")
                
        except Exception as e:
            logger.error(f"Error running fetal model {model}: {str(e)}", exc_info=True)
            results[model] = {"error": str(e)}
    
    return results


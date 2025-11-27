"""
Fetal Health Prediction with CatBoost and SHAP Explainability
Exact implementation matching the Colab notebook
"""

import numpy as np
import pandas as pd
import shap
from pathlib import Path
from catboost import CatBoostClassifier
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Feature names exactly as in notebook
FEATURES = [
    'baseline value', 'accelerations', 'fetal_movement', 'uterine_contractions',
    'light_decelerations', 'severe_decelerations', 'prolongued_decelerations',
    'abnormal_short_term_variability', 'mean_value_of_short_term_variability',
    'percentage_of_time_with_abnormal_long_term_variability',
    'mean_value_of_long_term_variability', 'histogram_width', 'histogram_min',
    'histogram_max', 'histogram_number_of_peaks', 'histogram_number_of_zeroes',
    'histogram_mode', 'histogram_mean', 'histogram_median', 'histogram_variance',
    'histogram_tendency'
]

# Class mapping
CLASS_LABELS = {
    1: 'Normal',
    2: 'Suspect',
    3: 'Pathological'
}


class FetalHealthAgent:
    """Agent for fetal health prediction with explainability"""
    
    def __init__(self, model_path: str):
        """Initialize agent with CatBoost model"""
        self.model = CatBoostClassifier()
        self.model.load_model(model_path)
        self.feature_names = FEATURES
        self.explainer = shap.TreeExplainer(self.model)
        logger.info("Fetal Health Agent initialized successfully")
    
    def predict(self, input_data: dict):
        """Make prediction on input data"""
        # Convert dict → numpy array (exact order as FEATURES)
        x = np.array([[input_data[feat] for feat in self.feature_names]])
        
        # Get prediction and probabilities
        prediction = self.model.predict(x)[0]
        probabilities = self.model.predict_proba(x)[0]
        
        return {
            "risk_level": int(prediction),
            "risk_label": CLASS_LABELS[int(prediction)],
            "probabilities": {
                "normal": float(probabilities[0]),
                "suspect": float(probabilities[1]),
                "pathological": float(probabilities[2])
            }
        }
    
    def explain(self, input_data: dict, top_n=10):
        """Generate SHAP explanations for prediction"""
        # Convert dict → numpy array
        x = np.array([[input_data[feat] for feat in self.feature_names]])
        
        # Compute SHAP values
        shap_values = self.explainer(x)
        
        # Get predicted class
        predicted_class = int(self.model.predict(x)[0])
        
        # Extract SHAP values for the predicted class
        values = shap_values.values[0, :, predicted_class - 1]  # -1 because CatBoost uses 0-indexed
        
        # Create feature importance dataframe
        feature_imp = []
        for i, feat in enumerate(self.feature_names):
            feature_imp.append({
                "feature": feat,
                "value": float(input_data[feat]),
                "importance": float(np.abs(values[i])),
                "impact": float(values[i]),
                "impact_direction": "increases_risk" if values[i] > 0 else "decreases_risk" if values[i] < 0 else "neutral"
            })
        
        # Sort by importance
        feature_imp.sort(key=lambda x: x["importance"], reverse=True)
        
        return {
            "predicted_class": predicted_class,
            "predicted_label": CLASS_LABELS[predicted_class],
            "top_features": feature_imp[:top_n],
            "base_value": float(self.explainer.expected_value[predicted_class - 1])
        }


async def predict_fetal_health(
    baseline_value,
    accelerations,
    fetal_movement,
    uterine_contractions,
    light_decelerations,
    severe_decelerations,
    prolongued_decelerations,
    abnormal_short_term_variability,
    mean_value_of_short_term_variability,
    percentage_of_time_with_abnormal_long_term_variability,
    mean_value_of_long_term_variability,
    histogram_width,
    histogram_min,
    histogram_max,
    histogram_number_of_peaks,
    histogram_number_of_zeroes,
    histogram_mode,
    histogram_mean,
    histogram_median,
    histogram_variance,
    histogram_tendency
):
    """
    Predict fetal health status with SHAP explainability
    Returns formatted text report for LLM processing
    """
    
    # Construct model path
    current_file = Path(__file__)
    model_path = str(current_file.parent / "FHP_1_catboost_model.cbm")
    
    # Initialize agent
    agent = await asyncio.to_thread(FetalHealthAgent, model_path)
    
    # Prepare input data
    input_data = {
        'baseline value': baseline_value,
        'accelerations': accelerations,
        'fetal_movement': fetal_movement,
        'uterine_contractions': uterine_contractions,
        'light_decelerations': light_decelerations,
        'severe_decelerations': severe_decelerations,
        'prolongued_decelerations': prolongued_decelerations,
        'abnormal_short_term_variability': abnormal_short_term_variability,
        'mean_value_of_short_term_variability': mean_value_of_short_term_variability,
        'percentage_of_time_with_abnormal_long_term_variability': percentage_of_time_with_abnormal_long_term_variability,
        'mean_value_of_long_term_variability': mean_value_of_long_term_variability,
        'histogram_width': histogram_width,
        'histogram_min': histogram_min,
        'histogram_max': histogram_max,
        'histogram_number_of_peaks': histogram_number_of_peaks,
        'histogram_number_of_zeroes': histogram_number_of_zeroes,
        'histogram_mode': histogram_mode,
        'histogram_mean': histogram_mean,
        'histogram_median': histogram_median,
        'histogram_variance': histogram_variance,
        'histogram_tendency': histogram_tendency
    }
    
    # Make prediction
    prediction_result = await asyncio.to_thread(agent.predict, input_data)
    
    # Generate explanation
    explanation_result = await asyncio.to_thread(agent.explain, input_data)
    
    # Format report
    report = await format_fetal_report(prediction_result, explanation_result, input_data)
    
    return report


async def format_fetal_report(prediction, explanation, input_data):
    """Format prediction and explanation as text report"""
    
    output = []
    
    # Header
    output.append("=" * 80)
    output.append("FHP REPORT")
    output.append("=" * 80)
    output.append("")
    
    # Prediction Summary
    output.append("CARDIOTOCOGRAPHY ANALYSIS:")
    output.append("-" * 80)
    output.append(f"Fetal Status: {prediction['risk_label'].upper()}")
    output.append(f"Risk Level: {prediction['risk_level']}")
    output.append("")
    output.append("Classification Confidence:")
    output.append(f"  • Normal:        {prediction['probabilities']['normal']:.1%}")
    output.append(f"  • Suspect:       {prediction['probabilities']['suspect']:.1%}")
    output.append(f"  • Pathological:  {prediction['probabilities']['pathological']:.1%}")
    output.append("")
    
    # Clinical Interpretation
    output.append("CLINICAL INTERPRETATION:")
    output.append("-" * 80)
    
    if prediction['risk_level'] == 1:
        output.append("✓ NORMAL - Fetal heart rate patterns appear healthy")
        output.append("  The cardiotocography shows reassuring fetal heart rate patterns.")
        output.append("  Continue routine monitoring as per protocol.")
    elif prediction['risk_level'] == 2:
        output.append("⚠ SUSPECT - Abnormal patterns detected, requires attention")
        output.append("  Some concerning features in fetal heart rate patterns.")
        output.append("  Recommend increased monitoring and clinical correlation.")
    else:
        output.append("⚠ PATHOLOGICAL - Significant abnormalities detected")
        output.append("  Fetal heart rate patterns show significant abnormalities.")
        output.append("  Immediate medical evaluation and intervention may be required.")
    
    output.append("")
    
    # SHAP Explanation
    output.append("EXPLAINABLE AI ANALYSIS (SHAP TreeExplainer):")
    output.append("-" * 80)
    output.append(f"Model Base Value: {explanation['base_value']:.4f}")
    output.append("")
    output.append("Top Contributing Features:")
    output.append("")
    
    for idx, feat in enumerate(explanation['top_features'], 1):
        impact_symbol = "[+]" if feat['impact_direction'] == 'increases_risk' else "[-]" if feat['impact_direction'] == 'decreases_risk' else "[•]"
        
        output.append(f"{idx:2d}. {impact_symbol} {feat['feature']}")
        output.append(f"    Measured Value: {feat['value']}")
        output.append(f"    SHAP Impact: {feat['impact']:+.4f}")
        output.append(f"    Importance: {feat['importance']:.4f}")
        output.append("")
    
    output.append("-" * 80)
    output.append("SHAP INTERPRETATION:")
    output.append("• SHAP values show how each CTG feature influenced this classification")
    output.append("• Positive impacts push prediction toward higher risk classification")
    output.append("• Negative impacts push prediction toward lower risk classification")
    output.append("• Base value represents the average model prediction across all data")
    output.append("")
    
    return "\n".join(output)


# Wrapper for agent integration
async def run_fetal_prediction(patient_data: dict) -> str:
    """
    Wrapper function that extracts features from patient_data dict
    and calls predict_fetal_health
    """
    return await predict_fetal_health(
        baseline_value=patient_data.get('baseline_value'),
        accelerations=patient_data.get('accelerations'),
        fetal_movement=patient_data.get('fetal_movement'),
        uterine_contractions=patient_data.get('uterine_contractions'),
        light_decelerations=patient_data.get('light_decelerations'),
        severe_decelerations=patient_data.get('severe_decelerations'),
        prolongued_decelerations=patient_data.get('prolongued_decelerations'),
        abnormal_short_term_variability=patient_data.get('abnormal_short_term_variability'),
        mean_value_of_short_term_variability=patient_data.get('mean_value_of_short_term_variability'),
        percentage_of_time_with_abnormal_long_term_variability=patient_data.get('percentage_of_time_with_abnormal_long_term_variability'),
        mean_value_of_long_term_variability=patient_data.get('mean_value_of_long_term_variability'),
        histogram_width=patient_data.get('histogram_width'),
        histogram_min=patient_data.get('histogram_min'),
        histogram_max=patient_data.get('histogram_max'),
        histogram_number_of_peaks=patient_data.get('histogram_number_of_peaks'),
        histogram_number_of_zeroes=patient_data.get('histogram_number_of_zeroes'),
        histogram_mode=patient_data.get('histogram_mode'),
        histogram_mean=patient_data.get('histogram_mean'),
        histogram_median=patient_data.get('histogram_median'),
        histogram_variance=patient_data.get('histogram_variance'),
        histogram_tendency=patient_data.get('histogram_tendency')
    )
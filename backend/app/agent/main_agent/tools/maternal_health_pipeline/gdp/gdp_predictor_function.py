"""
Gestational Diabetes Prediction with Explainable AI
Function-based interface that returns text output for LLM processing
"""

import numpy as np
import pandas as pd
import shap
from sklearn.neural_network import MLPClassifier
import warnings
from .model_loader import load_gdp_model
from .feature_scaler import normalize_features, FEATURE_RANGES
import asyncio
from pathlib import Path
import time
from ...helper.benchmark import record
warnings.filterwarnings('ignore')

# Feature names as per the model
FEATURE_NAMES = [
    'Age', 'BMI', 'Dia BP', 'HDL', 'Hemoglobin',
    'No of Pregnancy', 'OGTT', 'Sys BP',
    'Gestation in previous Pregnancy', 'Family History',
    'unexplained prenetal loss', 'Large Child or Birth Default',
    'PCOS', 'Sedentary Lifestyle', 'Prediabetes'
]

# ── Singleton cache ──────────────────────────────────────────
# Model is loaded once on first prediction call. Eliminates ~1.24s pkl load per request.
_gdm_model = None


def _get_gdm_model():
    """Return the cached GDM model, loading it on first call."""
    global _gdm_model
    if _gdm_model is None:
        current_file = Path(__file__)
        model_path = str(current_file.parent / "GDP_model.pkl")
        _t0 = time.perf_counter()
        _gdm_model = load_gdp_model(model_path)
        record("Model Load: GDM (pkl) [COLD]", time.perf_counter() - _t0)
    else:
        record("Model Load: GDM (pkl) [WARM]", 0.0)
    return _gdm_model


async def predict_gdm(
    age,
    bmi,
    dia_bp,
    hdl,
    hemoglobin,
    no_of_pregnancy,
    ogtt,
    sys_bp,
    gestation_in_previous_pregnancy,
    family_history,
    unexplained_prenatal_loss,
    large_child_or_birth_default,
    pcos,
    sedentary_lifestyle,
    prediabetes
):
    
    # Get cached model (loads on first call only)
    model = await asyncio.to_thread(_get_gdm_model)
    record("Model Load: GDM (pkl)", 0.0)  # Already tracked inside _get_gdm_model
    
    # Create input DataFrame with RAW values
    input_data = {
        'Age': age,
        'BMI': bmi,
        'Dia BP': dia_bp,
        'HDL': hdl,
        'Hemoglobin': hemoglobin,
        'No of Pregnancy': no_of_pregnancy,
        'OGTT': ogtt,
        'Sys BP': sys_bp,
        'Gestation in previous Pregnancy': gestation_in_previous_pregnancy,
        'Family History': family_history,
        'unexplained prenetal loss': unexplained_prenatal_loss,
        'Large Child or Birth Default': large_child_or_birth_default,
        'PCOS': pcos,
        'Sedentary Lifestyle': sedentary_lifestyle,
        'Prediabetes': prediabetes
    }
    
    input_df_raw = pd.DataFrame([input_data])
    
    
    # Normalize features for model prediction (model expects 0-1 scaled values)
    input_df_normalized = await asyncio.to_thread(normalize_features, input_df_raw)
    print(input_df_normalized)

    
    # Make prediction using NORMALIZED data
    prediction = await asyncio.to_thread(model.predict, input_df_normalized)
    prediction = prediction[0]
    prediction_proba = await asyncio.to_thread(model.predict_proba, input_df_normalized)
    prediction_proba = prediction_proba[0]
    
    # Generate SHAP explanations
    shap_available = False
    feature_impacts = []
    
    # Method 1: Weight-based importance (most reliable for this model)
    try:
        if hasattr(model, 'coefs_'):
            # Use input layer weights as importance proxy
            weights = np.abs(model.coefs_[0])  # Shape: (n_features, n_hidden)
            importance = weights.mean(axis=1)  # Average across hidden units
            
            # Get the actual prediction to determine direction
            feature_impacts = []
            for i, feature in enumerate(FEATURE_NAMES):
                imp_score = importance[i]
                feat_value = input_df_raw.iloc[0][feature]  # Use RAW value for display
                
                # For binary features, direction is based on value
                # For continuous, use weight magnitude
                if feat_value in [0, 1]:
                    direction = 'increases_risk' if feat_value == 1 and prediction == 1 else 'decreases_risk'
                else:
                    # Higher importance = more influence
                    direction = 'influences_prediction'
                
                feature_impacts.append({
                    'feature': feature,
                    'value': feat_value,  # Store RAW value
                    'shap_value': float(imp_score),
                    'impact_direction': direction,
                    'method': 'weight_based'
                })
            
            feature_impacts.sort(key=lambda x: abs(x['shap_value']), reverse=True)
            shap_available = 'weight_based'
            
            print(f"Using weight-based feature importance (most reliable for this model)")
        else:
            raise Exception("No weights available")
            
    except Exception as e:
        print(f"Weight-based importance failed: {e}")
        
        # Method 2: Try SHAP with proper background
        try:
            # Create synthetic background data by perturbing the input
            background_data = []
            for _ in range(50):
                perturbed = input_df_raw.copy()
                for col in input_df_raw.columns:
                    # Add random noise (±20% for continuous, flip for binary)
                    if input_df_raw[col].iloc[0] in [0, 1]:  # Binary feature
                        perturbed[col] = np.random.choice([0, 1])
                    else:  # Continuous feature
                        noise = np.random.uniform(0.8, 1.2)
                        perturbed[col] = input_df_raw[col] * noise
                background_data.append(perturbed)
            
            background_df = pd.concat(background_data, ignore_index=True)
            
            # Create explainer
            def model_predict(X):
                if isinstance(X, np.ndarray):
                    X = pd.DataFrame(X, columns=FEATURE_NAMES)
                return model.predict_proba(X)
            
            explainer = shap.KernelExplainer(model_predict, background_df)
            
            # Compute SHAP values
            shap_values = await asyncio.to_thread(explainer.shap_values, input_df_normalized, nsamples=100)
            
            # Get SHAP values for the positive class (GD)
            if isinstance(shap_values, list):
                shap_values_positive = shap_values[1][0]
            else:
                shap_values_positive = shap_values[0]
            
            # Check if SHAP values are meaningful
            if np.sum(np.abs(shap_values_positive)) > 0.001:
                # Create feature importance summary
                feature_impacts = []
                for i, feature in enumerate(FEATURE_NAMES):
                    impact = shap_values_positive[i]
                    feature_impacts.append({
                        'feature': feature,
                        'value': input_df_raw.iloc[0][feature],
                        'shap_value': float(impact),
                        'impact_direction': 'increases_risk' if impact > 0 else 'decreases_risk' if impact < 0 else 'neutral'
                    })
                
                # Sort by absolute SHAP value
                feature_impacts.sort(key=lambda x: abs(x['shap_value']), reverse=True)
                shap_available = True
            else:
                raise Exception("SHAP values are all zero")
            
        except Exception as e2:
            print(f"SHAP failed: {e2}")
            
            # Method 3: Use LIME as fallback
            try:
                from lime import lime_tabular
                
                # Create representative background data for LIME
                background_data = []
                for _ in range(100):
                    sample = {}
                    for feature in FEATURE_NAMES:
                        if input_df_raw[feature].iloc[0] in [0, 1]:  # Binary
                            sample[feature] = np.random.choice([0, 1])
                        else:  # Continuous
                            # Use reasonable ranges based on feature
                            if feature == 'Age':
                                sample[feature] = np.random.uniform(18, 50)
                            elif feature == 'BMI':
                                sample[feature] = np.random.uniform(15, 50)
                            elif 'BP' in feature:
                                sample[feature] = np.random.uniform(60, 150)
                            elif feature == 'HDL':
                                sample[feature] = np.random.uniform(20, 100)
                            elif feature == 'Hemoglobin':
                                sample[feature] = np.random.uniform(8, 18)
                            elif feature == 'OGTT':
                                sample[feature] = np.random.uniform(70, 200)
                            else:
                                sample[feature] = input_df_raw[feature].iloc[0] * np.random.uniform(0.5, 1.5)
                    background_data.append(sample)
                
                background_array = pd.DataFrame(background_data).values
                
                explainer = lime_tabular.LimeTabularExplainer(
                    background_array,
                    feature_names=FEATURE_NAMES,
                    class_names=['No GD', 'GD'],
                    mode='classification'
                )
                
                exp = await asyncio.to_thread(explainer.explain_instance,
                    input_df_raw.values[0],
                    model.predict_proba,
                    num_features=15
                )
                
                # Extract feature weights
                lime_weights = dict(exp.as_list())
                
                feature_impacts = []
                for i, feature in enumerate(FEATURE_NAMES):
                    # Find matching weight from LIME
                    weight = 0
                    for lime_feat, lime_weight in lime_weights.items():
                        if feature in lime_feat or any(char.isdigit() for char in lime_feat):
                            weight = lime_weight
                            break
                    
                    feature_impacts.append({
                        'feature': feature,
                        'value': input_df_raw.iloc[0][feature],
                        'shap_value': float(weight),
                        'impact_direction': 'increases_risk' if weight > 0 else 'decreases_risk',
                        'method': 'LIME'
                    })
                
                feature_impacts.sort(key=lambda x: abs(x['shap_value']), reverse=True)
                shap_available = 'lime'
                
            except Exception as e3:
                print(f"LIME failed: {e3}")
                shap_available = False
                feature_impacts = []
    
    # Prepare result dictionary
    result = {
        'prediction': 'positive' if prediction == 1 else 'negative',
        'prediction_label': 'High Risk of Gestational Diabetes' if prediction == 1 else 'Low Risk of Gestational Diabetes',
        'confidence_scores': {
            'no_gestational_diabetes': float(prediction_proba[0]),
            'gestational_diabetes': float(prediction_proba[1])
        },
        'patient_data': input_data,
        'feature_importance': feature_impacts,
        'shap_available': shap_available
    }
    
    return result


async def format_result_for_llm(result):
    """
    Format the prediction result as a structured text report for LLM processing
    
    Parameters:
    -----------
    result : dict
        Result dictionary from predict_gdm function
    
    Returns:
    --------
    str
        Formatted text report
    """
    
    output = []
    
    # Header
    output.append("=" * 80)
    output.append("GESTATIONAL DIABETES PREDICTION REPORT")
    output.append("=" * 80)
    output.append("")
    
    # Prediction Summary
    output.append("PREDICTION SUMMARY:")
    output.append("-" * 80)
    output.append(f"Overall Assessment: {result['prediction_label']}")
    output.append(f"Prediction: {result['prediction'].upper()}")
    output.append(f"Confidence - No GD: {result['confidence_scores']['no_gestational_diabetes']:.1%}")
    output.append(f"Confidence - GD Present: {result['confidence_scores']['gestational_diabetes']:.1%}")
    output.append("")

    
    # Feature Importance (SHAP Analysis)
    if result['shap_available'] and result['feature_importance']:
        if result['shap_available'] == 'lime':
            output.append("EXPLAINABLE AI ANALYSIS (LIME - Local Interpretable Model):")
        elif result['shap_available'] == 'weight_based':
            output.append("EXPLAINABLE AI ANALYSIS (Neural Network Weight Analysis):")
        elif result['shap_available'] == 'permutation':
            output.append("EXPLAINABLE AI ANALYSIS (Permutation Importance):")
        else:
            output.append("EXPLAINABLE AI ANALYSIS (SHAP Values):")
        output.append("-" * 80)
        output.append("Features ranked by their impact on the prediction:")
        output.append("")
        
        for idx, feat in enumerate(result['feature_importance'], 1):
            if 'method' in feat:
                if feat['method'] == 'LIME':
                    impact_symbol = "[+]" if feat['impact_direction'] == 'increases_risk' else "[-]"
                    impact_text = "INCREASES RISK" if feat['impact_direction'] == 'increases_risk' else "DECREASES RISK"
                elif feat['method'] in ['weight_based', 'permutation_importance']:
                    impact_symbol = "[*]"
                    impact_text = "INFLUENCES PREDICTION"
                else:
                    impact_symbol = "[?]"
                    impact_text = feat['impact_direction'].upper().replace('_', ' ')
            else:
                impact_symbol = "[+]" if feat['impact_direction'] == 'increases_risk' else "[-]" if feat['impact_direction'] == 'decreases_risk' else "[0]"
                impact_text = "INCREASES RISK" if feat['impact_direction'] == 'increases_risk' else "DECREASES RISK" if feat['impact_direction'] == 'decreases_risk' else "NEUTRAL"
            
            output.append(f"{idx:2d}. {impact_symbol} {feat['feature']}")
            output.append(f"    Value: {feat['value']}")
            output.append(f"    Importance Score: {feat['shap_value']:+.6f}")
            output.append(f"    Impact: {impact_text}")
            output.append("")
        
        output.append("-" * 80)
        output.append("INTERPRETATION NOTES:")
        if result['shap_available'] == 'lime':
            output.append("- LIME shows how each feature contributes to this specific prediction")
            output.append("- Positive scores increase GD risk, negative scores decrease it")
        elif result['shap_available'] == 'weight_based':
            output.append("- Scores based on neural network layer weights")
            output.append("- Higher scores mean the feature has more influence in the model")
        elif result['shap_available'] == 'permutation':
            output.append("- Scores show how much each feature influences the prediction")
            output.append("- Higher scores mean the feature has more impact on the model's decision")
        else:
            output.append("- Positive values indicate features that increase GD risk")
            output.append("- Negative values indicate features that decrease GD risk")
            output.append("- Larger absolute values mean stronger influence on the prediction")
        output.append("")
    else:
        output.append("EXPLAINABLE AI ANALYSIS:")
        output.append("-" * 80)
        output.append("Detailed feature explanations are not available for this prediction.")
        output.append("However, the prediction is based on all 15 input features.")
        output.append("")
    
    # Footer
    output.append("=" * 80)
    output.append("END OF REPORT")
    output.append("=" * 80)
    
    return "\n".join(output)

async def predict_gdp(
    age,
    bmi,
    dia_bp,
    hdl,
    hemoglobin,
    no_of_pregnancy,
    ogtt,
    sys_bp,
    gestation_in_previous_pregnancy,
    family_history,
    unexplained_prenatal_loss,
    large_child_or_birth_default,
    pcos,
    sedentary_lifestyle,
    prediabetes
):
    """Return the model outcome and its human-readable report."""

    result = await predict_gdm(
        age=age,
        bmi=bmi,
        dia_bp=dia_bp,
        hdl=hdl,
        hemoglobin=hemoglobin,
        no_of_pregnancy=no_of_pregnancy,
        ogtt=ogtt,
        sys_bp=sys_bp,
        gestation_in_previous_pregnancy=gestation_in_previous_pregnancy,
        family_history=family_history,
        unexplained_prenatal_loss=unexplained_prenatal_loss,
        large_child_or_birth_default=large_child_or_birth_default,
        pcos=pcos,
        sedentary_lifestyle=sedentary_lifestyle,
        prediabetes=prediabetes
    )

    formatted_report = await format_result_for_llm(result)
    probabilities = result["confidence_scores"]
    predicted_class = result["prediction"]
    return {
        "status": "completed",
        "outcome": result["prediction_label"],
        "severity": "high" if predicted_class == "positive" else "low",
        "predicted_class": predicted_class,
        "confidence": max(probabilities.values()),
        "probabilities": probabilities,
        "report": formatted_report,
    }

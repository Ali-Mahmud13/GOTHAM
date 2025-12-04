"""
Explainability for fetal health predictions
"""

import numpy as np
import asyncio


def get_feature_names():
    """Return list of feature names in correct order"""
    return [
        'baseline value',
        'accelerations',
        'fetal_movement',
        'uterine_contractions',
        'light_decelerations',
        'severe_decelerations',
        'prolongued_decelerations',
        'abnormal_short_term_variability',
        'mean_value_of_short_term_variability',
        'percentage_of_time_with_abnormal_long_term_variability',
        'mean_value_of_long_term_variability',
        'histogram_width',
        'histogram_min',
        'histogram_max',
        'histogram_number_of_peaks',
        'histogram_number_of_zeroes',
        'histogram_mode',
        'histogram_mean',
        'histogram_median',
        'histogram_variance',
        'histogram_tendency'
    ]


async def generate_explanations(model, input_df, predicted_class):
    """
    Generate feature importance explanations
    
    Parameters:
    -----------
    model : trained model
        The prediction model
    input_df : pd.DataFrame
        Input features
    predicted_class : int
        Predicted class (1, 2, or 3)
    
    Returns:
    --------
    list: Feature importance information
    """
    
    feature_names = get_feature_names()
    feature_importance = []
    
    try:
        # Method 1: Try SHAP (tree models)
        import shap
        
        explainer = shap.TreeExplainer(model)
        shap_values = await asyncio.to_thread(explainer.shap_values, input_df)
        
        # Get SHAP values for predicted class
        if isinstance(shap_values, list):
            class_shap_values = shap_values[predicted_class - 1][0]
        else:
            class_shap_values = shap_values[0]
        
        for i, feature in enumerate(feature_names):
            impact = class_shap_values[i]
            
            feature_importance.append({
                'feature': feature,
                'value': float(input_df.iloc[0][feature]),
                'shap_value': float(impact),
                'impact_direction': 'increases_risk' if impact > 0 else 'decreases_risk' if impact < 0 else 'neutral',
                'method': 'shap'
            })
        
        feature_importance.sort(key=lambda x: abs(x['shap_value']), reverse=True)
        return feature_importance
        
    except Exception as e:
        print(f"SHAP failed: {e}")
        
        # Method 2: Fallback to feature_importances_ if available
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                
                for i, feature in enumerate(feature_names):
                    feature_importance.append({
                        'feature': feature,
                        'value': float(input_df.iloc[0][feature]),
                        'shap_value': float(importances[i]),
                        'impact_direction': 'influences_prediction',
                        'method': 'feature_importance'
                    })
                
                feature_importance.sort(key=lambda x: abs(x['shap_value']), reverse=True)
                return feature_importance
        except Exception as e2:
            print(f"Feature importance failed: {e2}")
        
        # Method 3: If all fails, return basic info
        for i, feature in enumerate(feature_names):
            feature_importance.append({
                'feature': feature,
                'value': float(input_df.iloc[0][feature]),
                'shap_value': 0.0,
                'impact_direction': 'unknown',
                'method': 'none'
            })
        
        return feature_importance
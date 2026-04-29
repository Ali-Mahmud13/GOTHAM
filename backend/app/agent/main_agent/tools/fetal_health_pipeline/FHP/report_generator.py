"""
Generate formatted text reports for fetal health predictions
"""

import asyncio


async def format_prediction_report(result):
    """
    Format prediction result as structured text report
    
    Parameters:
    -----------
    result : dict
        Prediction results with all details
    
    Returns:
    --------
    str
        Formatted text report
    """
    
    output = []
    
    # Header
    output.append("=" * 80)
    output.append("FETAL HEALTH ASSESSMENT REPORT")
    output.append("=" * 80)
    output.append("")
    
    # Prediction Summary
    output.append("CARDIOTOCOGRAPHY ANALYSIS:")
    output.append("-" * 80)
    output.append(f"Fetal Status: {result['prediction_label'].upper()}")
    output.append("")
    output.append("Classification Confidence:")
    output.append(f"  • Normal:        {result['confidence_scores']['normal']:.1%}")
    output.append(f"  • Suspect:       {result['confidence_scores']['suspect']:.1%}")
    output.append(f"  • Pathological:  {result['confidence_scores']['pathological']:.1%}")
    output.append("")
    
    # Clinical Interpretation
    output.append("CLINICAL INTERPRETATION:")
    output.append("-" * 80)
    
    if result['prediction'] == 1:
        output.append("✓ NORMAL - Fetal heart rate patterns appear healthy")
        output.append("  The cardiotocography shows reassuring fetal heart rate patterns.")
        output.append("  Continue routine monitoring as per protocol.")
    elif result['prediction'] == 2:
        output.append("⚠ SUSPECT - Abnormal patterns detected, requires attention")
        output.append("  Some concerning features in fetal heart rate patterns.")
        output.append("  Recommend increased monitoring and clinical correlation.")
    else:
        output.append("⚠ PATHOLOGICAL - Significant abnormalities detected")
        output.append("  Fetal heart rate patterns show significant abnormalities.")
        output.append("  Immediate medical evaluation and intervention may be required.")
    
    output.append("")
    
    # Feature Importance
    if result['feature_importance']:
        output.append("KEY CONTRIBUTING FACTORS:")
        output.append("-" * 80)
        output.append("Features ranked by their impact on this assessment:")
        output.append("")
        
        for idx, feat in enumerate(result['feature_importance'][:10], 1):  # Top 10
            impact_symbol = "[+]" if feat['impact_direction'] == 'increases_risk' else "[-]" if feat['impact_direction'] == 'decreases_risk' else "[•]"
            
            output.append(f"{idx:2d}. {impact_symbol} {feat['feature']}")
            output.append(f"    Measured Value: {feat['value']:.2f}")
            output.append(f"    Impact Score: {feat['shap_value']:+.4f}")
            output.append("")
        
        output.append("-" * 80)
        output.append("INTERPRETATION NOTES:")
        if result['feature_importance'][0].get('method') == 'shap':
            output.append("• SHAP analysis shows how each CTG feature influenced this classification")
            output.append("• Positive scores increase risk classification")
            output.append("• Negative scores indicate protective or reassuring features")
        else:
            output.append("• Importance scores show relative influence of each feature")
            output.append("• Higher scores indicate stronger impact on classification")
        output.append("")
    
    # Footer
    output.append("=" * 80)
    output.append("DISCLAIMER:")
    output.append("This is an AI-assisted assessment tool. All findings should be")
    output.append("interpreted by qualified healthcare professionals in clinical context.")
    output.append("=" * 80)
    
    return "\n".join(output)
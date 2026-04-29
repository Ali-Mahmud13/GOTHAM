"""
Test script for Fetal Health Prediction
Mimics the notebook's testing approach
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from FHP_predictor import (
    predict_fetal_health,
    FetalHealthAgent,
    FEATURES
)


async def test_basic_prediction():
    """Test basic prediction functionality"""
    print("=" * 80)
    print("TEST 1: Basic Prediction")
    print("=" * 80)
    
    # Sample from notebook
    sample = {
        'baseline_value': 120,
        'accelerations': 0.003,
        'fetal_movement': 0.004,
        'uterine_contractions': 0.001,
        'light_decelerations': 0.0,
        'severe_decelerations': 0.0,
        'prolongued_decelerations': 0.0,
        'abnormal_short_term_variability': 12,
        'mean_value_of_short_term_variability': 2.0,
        'percentage_of_time_with_abnormal_long_term_variability': 30,
        'mean_value_of_long_term_variability': 20,
        'histogram_width': 60,
        'histogram_min': 50,
        'histogram_max': 160,
        'histogram_number_of_peaks': 2,
        'histogram_number_of_zeroes': 0,
        'histogram_mode': 120,
        'histogram_mean': 130,
        'histogram_median': 125,
        'histogram_variance': 20,
        'histogram_tendency': 0
    }
    
    print("\n📊 Input Sample:")
    for key, value in sample.items():
        print(f"  {key}: {value}")
    
    print("\n🔄 Making prediction...")
    
    # Get full report
    report = await predict_fetal_health(**sample)
    
    print("\n" + report)
    print("\n✅ Test 1 Complete")


async def test_agent_directly():
    """Test the agent class directly (like notebook)"""
    print("\n" + "=" * 80)
    print("TEST 2: Direct Agent Testing (Notebook Style)")
    print("=" * 80)
    
    # Initialize agent
    current_file = Path(__file__)
    model_path = current_file.parent /"FHP_1_catboost_model.cbm"
    
    print(f"\n📁 Loading model from: {model_path}")
    agent = FetalHealthAgent(str(model_path))
    
    # Sample data
    sample = {
        'baseline value': 120,
        'accelerations': 0.003,
        'fetal_movement': 0.004,
        'uterine_contractions': 0.001,
        'light_decelerations': 0.0,
        'severe_decelerations': 0.0,
        'prolongued_decelerations': 0.0,
        'abnormal_short_term_variability': 12,
        'mean_value_of_short_term_variability': 2.0,
        'percentage_of_time_with_abnormal_long_term_variability': 30,
        'mean_value_of_long_term_variability': 20,
        'histogram_width': 60,
        'histogram_min': 50,
        'histogram_max': 160,
        'histogram_number_of_peaks': 2,
        'histogram_number_of_zeroes': 0,
        'histogram_mode': 120,
        'histogram_mean': 130,
        'histogram_median': 125,
        'histogram_variance': 20,
        'histogram_tendency': 0
    }
    
    # Test prediction
    print("\n🩺 Running Prediction...")
    prediction = agent.predict(sample)
    print(f"Prediction: {prediction}")
    
    # Test explanation
    print("\n🔍 Running XAI Explanation...")
    explanation = agent.explain(sample)
    print(f"\nPredicted Class: {explanation['predicted_class']} ({explanation['predicted_label']})")
    print(f"Base Value: {explanation['base_value']:.4f}")
    print("\nTop 5 Contributing Features:")
    for idx, feat in enumerate(explanation['top_features'][:5], 1):
        impact_dir = "↑" if feat['impact'] > 0 else "↓" if feat['impact'] < 0 else "→"
        print(f"  {idx}. {feat['feature']}: {feat['value']} "
              f"[SHAP: {feat['impact']:+.4f} {impact_dir}]")
    
    print("\n✅ Test 2 Complete")


async def test_multiple_scenarios():
    """Test with different scenarios"""
    print("\n" + "=" * 80)
    print("TEST 3: Multiple Clinical Scenarios")
    print("=" * 80)
    
    scenarios = [
        {
            "name": "Normal Case",
            "data": {
                'baseline value': 120,
                'accelerations': 0.005,
                'fetal_movement': 0.006,
                'uterine_contractions': 0.002,
                'light_decelerations': 0.0,
                'severe_decelerations': 0.0,
                'prolongued_decelerations': 0.0,
                'abnormal_short_term_variability': 10,
                'mean_value_of_short_term_variability': 3.0,
                'percentage_of_time_with_abnormal_long_term_variability': 20,
                'mean_value_of_long_term_variability': 25,
                'histogram_width': 70,
                'histogram_min': 60,
                'histogram_max': 170,
                'histogram_number_of_peaks': 3,
                'histogram_number_of_zeroes': 0,
                'histogram_mode': 125,
                'histogram_mean': 130,
                'histogram_median': 128,
                'histogram_variance': 15,
                'histogram_tendency': 0
            }
        },
        {
            "name": "Suspect Case",
            "data": {
                'baseline value': 110,
                'accelerations': 0.002,
                'fetal_movement': 0.003,
                'uterine_contractions': 0.004,
                'light_decelerations': 0.002,
                'severe_decelerations': 0.0,
                'prolongued_decelerations': 0.0,
                'abnormal_short_term_variability': 20,
                'mean_value_of_short_term_variability': 1.5,
                'percentage_of_time_with_abnormal_long_term_variability': 45,
                'mean_value_of_long_term_variability': 15,
                'histogram_width': 50,
                'histogram_min': 40,
                'histogram_max': 150,
                'histogram_number_of_peaks': 1,
                'histogram_number_of_zeroes': 1,
                'histogram_mode': 110,
                'histogram_mean': 115,
                'histogram_median': 113,
                'histogram_variance': 25,
                'histogram_tendency': -1
            }
        },
        {
            "name": "Pathological Case",
            "data": {
                'baseline value': 100,
                'accelerations': 0.001,
                'fetal_movement': 0.001,
                'uterine_contractions': 0.006,
                'light_decelerations': 0.003,
                'severe_decelerations': 0.002,
                'prolongued_decelerations': 0.001,
                'abnormal_short_term_variability': 30,
                'mean_value_of_short_term_variability': 1.0,
                'percentage_of_time_with_abnormal_long_term_variability': 60,
                'mean_value_of_long_term_variability': 10,
                'histogram_width': 40,
                'histogram_min': 30,
                'histogram_max': 140,
                'histogram_number_of_peaks': 1,
                'histogram_number_of_zeroes': 2,
                'histogram_mode': 100,
                'histogram_mean': 105,
                'histogram_median': 103,
                'histogram_variance': 35,
                'histogram_tendency': -1
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'─' * 80}")
        print(f"Testing: {scenario['name']}")
        print(f"{'─' * 80}")
        
        report = await predict_fetal_health(**scenario['data'])
        
        # Extract just the prediction summary
        lines = report.split('\n')
        for i, line in enumerate(lines):
            if 'CARDIOTOCOGRAPHY ANALYSIS:' in line:
                # Print next 6 lines
                for j in range(i, min(i+8, len(lines))):
                    print(lines[j])
                break
    
    print("\n✅ Test 3 Complete")


async def main():
    """Run all tests"""
    print("\n" + "🧪" * 40)
    print("FETAL HEALTH PREDICTION - TEST SUITE")
    print("🧪" * 40 + "\n")
    
    try:
        # Run tests
        await test_basic_prediction()
        await test_agent_directly()
        await test_multiple_scenarios()
        
        print("\n" + "✅" * 40)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("✅" * 40 + "\n")
        
    except Exception as e:
        print("\n" + "❌" * 40)
        print(f"TEST FAILED: {e}")
        print("❌" * 40 + "\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""Test GDP model loading"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agent.main_agent.tools.maternal_health_pipeline.gdp.model_loader import load_gdp_model

def test_model_loading():
    model_path = 'app/agent/main_agent/tools/maternal_health_pipeline/gdp/GDP_model.pkl'
    
    print("="*70)
    print("TESTING GDP MODEL LOADING")
    print("="*70)
    
    try:
        print(f"\n📁 Loading model from: {model_path}")
        model = load_gdp_model(model_path)
        
        print("✅ SUCCESS! Model loaded successfully")
        print(f"   Model type: {type(model)}")
        print(f"   Model class: {model.__class__.__name__}")
        
        # Try to get model attributes
        if hasattr(model, 'n_features_in_'):
            print(f"   Features: {model.n_features_in_}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED to load model")
        print(f"   Error: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    success = test_model_loading()
    sys.exit(0 if success else 1)

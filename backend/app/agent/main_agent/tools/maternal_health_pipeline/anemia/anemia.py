# anemia.py - Main entry point for the anemia prediction module
from .anemiaxai import AnemiaXAI
import pandas as pd
from pathlib import Path

def generate_anemia_xai_report(WBC, RBC, HGB, HCT, MCV, MCH, MCHC, PLT):
    
    # Validate required features (all must be provided and non-null)
    required_features = [WBC, RBC, HGB, HCT, MCV, MCH, MCHC, PLT]
    if None in required_features or any(pd.isna(r) for r in required_features):
        raise ValueError("All required features (WBC, RBC, HGB, HCT, MCV, MCH, MCHC, PLT) must be provided and non-null for anemia prediction.")
    
    # Build features dict internally for compatibility with AnemiaXAI
    features = {
        'WBC': WBC,
        'RBC': RBC,
        'HGB': HGB,
        'HCT': HCT,
        'MCV': MCV,
        'MCH': MCH,
        'MCHC': MCHC,
        'PLT': PLT
    }
    current_file = Path(__file__)
    model_path = str(current_file.parent / "catboost_ovr_model.pkl")
    label_encoder_path=str(current_file.parent / "label_encoder.pkl")
    # Initialize AnemiaXAI with optional paths
    xai = AnemiaXAI(model_path=model_path,
                    label_encoder_path=label_encoder_path if label_encoder_path else 'label_encoder.pkl')

    # Generate Markdown report
    md_report = xai.generate_markdown_report(features)
    return md_report


# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    model_path = 'D:/School/FYP/GOTHAM/backend/app/agent/main_agent/tools/maternal_health_pipeline/anemia/catboost_ovr_model.pkl'
    label_encoder_path = 'D:/School/FYP/GOTHAM/backend/app/agent/main_agent/tools/maternal_health_pipeline/anemia/label_encoder.pkl'
    # Example: Pass features individually (simulating agent input)
    report = generate_anemia_xai_report(
        WBC=5.2, RBC=4.85, HGB=13.2, HCT=41, MCV=84.7, MCH=27.2, MCHC=32.1, PLT=181,
    )
    
    print(report)  # Markdown output
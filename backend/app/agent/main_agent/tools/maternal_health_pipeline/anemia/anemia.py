# anemia.py - Main entry point for the anemia prediction module
from .anemiaxai import AnemiaXAI
import pandas as pd
from pathlib import Path
import time
from ...helper.benchmark import record

# ── Singleton cache ──────────────────────────────────────────
# AnemiaXAI is the most expensive init: pkl load + shap.TreeExplainer build (~4.85s).
# Cached once, reused forever.
_anemia_xai: AnemiaXAI | None = None


def _get_anemia_xai() -> AnemiaXAI:
    """Return the cached AnemiaXAI instance, building it on first call."""
    global _anemia_xai
    if _anemia_xai is None:
        current_file = Path(__file__)
        model_path = str(current_file.parent / "catboost_ovr_model.pkl")
        label_encoder_path = str(current_file.parent / "label_encoder.pkl")
        _t0 = time.perf_counter()
        _anemia_xai = AnemiaXAI(
            model_path=model_path,
            label_encoder_path=label_encoder_path
        )
        record("Model Load: Anemia (pkl + SHAP explainers) [COLD]", time.perf_counter() - _t0)
    else:
        record("Model Load: Anemia (pkl + SHAP explainers) [WARM]", 0.0)
    return _anemia_xai

def generate_anemia_xai_report(WBC, RBC, HGB, HCT, MCV, MCH, MCHC, PLT):
    
    # Validate required features (all must be provided and non-null)
    required_features = [WBC, RBC, HGB, HCT, MCV, MCH, MCHC, PLT]
    if None in required_features or any(pd.isna(r) for r in required_features):
        raise ValueError("All required features (WBC, RBC, HGB, HCT, MCV, MCH, MCHC, PLT) must be provided and non-null for anemia prediction.")
    
    # Build features dict internally for compatibility with AnemiaXAI
    features = {
        'WBC': WBC, 'RBC': RBC, 'HGB': HGB, 'HCT': HCT,
        'MCV': MCV, 'MCH': MCH, 'MCHC': MCHC, 'PLT': PLT
    }

    # Get cached AnemiaXAI (loads + builds SHAP explainers on first call only)
    xai = _get_anemia_xai()

    diagnosis, probabilities, _ = xai.predict_anemia(features)

    # Generate Markdown report
    _t1 = time.perf_counter()
    md_report = xai.generate_markdown_report(features)
    record("Inference: Anemia predict() + SHAP", time.perf_counter() - _t1)
    return {
        "status": "completed",
        "outcome": diagnosis,
        "severity": "low" if diagnosis.strip().lower() == "healthy" else "high",
        "predicted_class": diagnosis,
        "confidence": float(max(probabilities.values())),
        "probabilities": {key: float(value) for key, value in probabilities.items()},
        "report": md_report,
    }


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

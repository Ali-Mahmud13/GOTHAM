from pathlib import Path

import pandas as pd

from .mmxai import MaternalHealthXAI


def generate_xai_report(model_path, Age, SystolicBP, DiastolicBP, BS, BodyTemp, HeartRate,
                        patient_id="Patient_001"):
    required = [Age, SystolicBP, DiastolicBP, BS, BodyTemp, HeartRate]
    if None in required or any(pd.isna(r) for r in required):
        raise ValueError("All features must be non-null.")
    
    features = {
        'Age': Age,
        'SystolicBP': SystolicBP,
        'DiastolicBP': DiastolicBP,
        'BS': BS,
        'BodyTemp': BodyTemp,
        'HeartRate': HeartRate
    }
    
    xai = MaternalHealthXAI(model_path)
    label, probabilities, _ = xai.predict_risk(features)
    report = xai.generate_markdown_report(features, patient_id)
    severity = {
        "Low Risk": "low",
        "Mid Risk": "medium",
        "High Risk": "high",
    }[label]
    return {
        "status": "completed",
        "outcome": label,
        "severity": severity,
        "predicted_class": label,
        "confidence": float(max(probabilities.values())),
        "probabilities": {key: float(value) for key, value in probabilities.items()},
        "report": report,
    }

# Example usage
if __name__ == "__main__":
    model_path = Path(__file__).resolve().parent / "maternal_health_model.pkl"
    
    report = generate_xai_report(
        model_path,
        Age=23, SystolicBP=90, DiastolicBP=60, BS=7.01, BodyTemp=98, HeartRate=76,
        patient_id="TEST_001"
    )
    
    print("=== Maternal Health XAI Report ===\n")
    print(report)

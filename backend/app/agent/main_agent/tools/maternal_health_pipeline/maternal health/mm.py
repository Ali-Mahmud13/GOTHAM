from mmxai import MaternalHealthXAI
import pandas as pd

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
    return xai.generate_markdown_report(features, patient_id)

# Example usage
if __name__ == "__main__":
    model_path = "maternal_health_model.pkl"
    
    report = generate_xai_report(
        model_path,
        Age=23, SystolicBP=90, DiastolicBP=60, BS=7.01, BodyTemp=98, HeartRate=76,
        patient_id="TEST_001"
    )
    
    print("=== Maternal Health XAI Report ===\n")
    print(report)
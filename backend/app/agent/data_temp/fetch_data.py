import pandas as pd
from pathlib import Path

# Get absolute path relative to this file
current_file = Path(__file__)
DATA_PATH = current_file.parent / "GDP_testing_data.csv"

async def fetch_patient_data(patient_identifier: str) -> dict:
    df = pd.read_csv(DATA_PATH)
    
    patient_row = df[
        (df['Patient_ID'].astype(str) == str(patient_identifier))
    ]
    
    if patient_row.empty:
        return {}
    
    return patient_row.iloc[0].to_dict()
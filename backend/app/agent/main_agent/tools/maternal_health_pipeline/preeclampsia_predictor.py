"""Async wrapper for the Preeclampsia / Maternal Health risk model.

The underlying model lives in the 'maternal health' directory (space in name
prevents normal Python imports), so we load it via importlib.
"""

import importlib.util
from pathlib import Path

_MM_DIR = Path(__file__).parent / "maternal health"
_MODEL_PATH = str(_MM_DIR / "maternal_health_model.pkl")

_spec = importlib.util.spec_from_file_location("mm", _MM_DIR / "mm.py")
_mm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mm)


async def predict_preeclampsia(Age, sys_bp, dia_bp, glucose_level, body_temp, heart_rate) -> str:
    """Run the Preeclampsia risk model and return a markdown report.

    Parameter names match the mm-contract.yml required_features keys so that
    clean_data_for_model passes them through correctly.
    """
    return _mm.generate_xai_report(
        model_path=_MODEL_PATH,
        Age=Age,
        SystolicBP=sys_bp,
        DiastolicBP=dia_bp,
        BS=glucose_level,
        BodyTemp=body_temp,
        HeartRate=heart_rate,
    )

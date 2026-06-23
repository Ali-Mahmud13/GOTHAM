"""Async wrapper for the Preeclampsia / Maternal Health risk model."""

from pathlib import Path

from .maternal_health.mm import generate_xai_report

_MODEL_PATH = Path(__file__).parent / "maternal_health" / "maternal_health_model.pkl"


def _mg_dl_to_mmol_l(value: float) -> float:
    """Convert the application's canonical glucose unit to the model training unit."""
    return float(value) / 18.0182


def _celsius_to_fahrenheit(value: float) -> float:
    """Convert the application's canonical temperature unit to the model training unit."""
    return (float(value) * 9 / 5) + 32


async def predict_preeclampsia(Age, sys_bp, dia_bp, glucose_level, body_temp, heart_rate) -> dict:
    """Run the Preeclampsia risk model and return a markdown report.

    Parameter names match the mm-contract.yml required_features keys so that
    clean_data_for_model passes them through correctly. The application stores
    glucose in mg/dL and temperature in °C, while the model was trained on
    mmol/L and °F, so conversion happens only at this model boundary.
    """
    return generate_xai_report(
        model_path=_MODEL_PATH,
        Age=Age,
        SystolicBP=sys_bp,
        DiastolicBP=dia_bp,
        BS=_mg_dl_to_mmol_l(glucose_level),
        BodyTemp=_celsius_to_fahrenheit(body_temp),
        HeartRate=heart_rate,
    )

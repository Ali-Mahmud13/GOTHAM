"""Helpers for the structured result contract shared by model nodes."""

from __future__ import annotations

from typing import Any


def normalize_feature_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def attach_input_metadata(
    result: dict[str, Any],
    cleaned_data: dict[str, Any],
    patient_data: dict[str, Any],
) -> dict[str, Any]:
    provenance_by_key = patient_data.get("_input_provenance") or {}
    normalized_provenance = {
        normalize_feature_name(key): value
        for key, value in provenance_by_key.items()
    }
    input_provenance: dict[str, Any] = {}

    for feature in cleaned_data:
        source = normalized_provenance.get(normalize_feature_name(feature))
        if source:
            input_provenance[feature] = source

    dynamic_ages = [
        int(source["age_days"])
        for source in input_provenance.values()
        if source.get("age_days") is not None
    ]
    result["input_snapshot"] = dict(cleaned_data)
    result["input_provenance"] = input_provenance
    result["oldest_input_age_days"] = max(dynamic_ages) if dynamic_ages else None
    result["has_stale_inputs"] = any(
        source.get("freshness") == "stale" for source in input_provenance.values()
    )
    return result


def incomplete_result(
    model_key: str,
    model_name: str,
    cleaned_data: dict[str, Any],
    patient_data: dict[str, Any],
) -> dict[str, Any]:
    missing_fields = [key for key, value in cleaned_data.items() if value is None]
    return attach_input_metadata(
        {
            "model": model_key,
            "status": "incomplete",
            "outcome": None,
            "severity": None,
            "predicted_class": None,
            "confidence": None,
            "probabilities": {},
            "missing_fields": missing_fields,
            "report": (
                f"## {model_name}\n\n"
                f"**Incomplete Data**\nMissing fields: {', '.join(missing_fields)}\n"
            ),
        },
        cleaned_data,
        patient_data,
    )


def failed_result(model_key: str, model_name: str, message: str) -> dict[str, Any]:
    return {
        "model": model_key,
        "status": "failed",
        "outcome": None,
        "severity": None,
        "predicted_class": None,
        "confidence": None,
        "probabilities": {},
        "missing_fields": [],
        "input_snapshot": {},
        "input_provenance": {},
        "oldest_input_age_days": None,
        "has_stale_inputs": False,
        "report": f"## {model_name}\n\n**Prediction Error**\n{message}\n",
    }

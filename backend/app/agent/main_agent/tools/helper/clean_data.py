import yaml

async def clean_data_for_model(patient_data: dict, contract_path: str) -> dict:
    # Normalize keys to lowercase snake_case for lookup
    normalized_data = {}
    for key, value in patient_data.items():
        normalized_key = (
            key.strip()
               .lower()
               .replace(" ", "_")
               .replace("-", "_")
        )
        normalized_data[normalized_key] = value

    # Load contract
    with open(contract_path, 'r') as f:
        contract = yaml.safe_load(f)
    
    required_features = contract.get('required_features', [])

    # Collect required features - normalize feature names for lookup,
    # but return with ORIGINAL contract feature names (case-sensitive)
    cleaned_data = {}
    for feature in required_features:
        # Normalize feature name for lookup in patient_data
        normalized_feature = (
            feature.strip()
                   .lower()
                   .replace(" ", "_")
                   .replace("-", "_")
        )
        # Use original feature name as key, but lookup by normalized name
        cleaned_data[feature] = normalized_data.get(normalized_feature)

    return cleaned_data


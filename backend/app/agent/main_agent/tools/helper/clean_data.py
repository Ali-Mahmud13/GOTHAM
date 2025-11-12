import yaml

async def clean_data_for_model(patient_data: dict, contract_path: str) -> dict:
    # Normalize keys to lowercase snake_case
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

    # Collect only required features
    cleaned_data = {feature: normalized_data.get(feature) for feature in required_features}

    return cleaned_data

import json
import os
from src.config.settings import LOCAL_ID_FILE

def load_uploaded_ids():
    """Load locally stored uploaded vector IDs."""
    if os.path.exists(LOCAL_ID_FILE):
        with open(LOCAL_ID_FILE, "r") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()


def save_uploaded_ids(vector_ids):
    """Save uploaded vector IDs to local JSON file."""
    with open(LOCAL_ID_FILE, "w") as f:
        json.dump(list(vector_ids), f)
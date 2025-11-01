# src/utils/local_ids.py

import json
from pathlib import Path

# track which chunks have already been embedded/uploaded
LOCAL_IDS_FILE = Path("local_ids.json")

def load_uploaded_ids():
    if not LOCAL_IDS_FILE.exists():
        # create empty dict if file doesn't exist
        save_uploaded_ids({"chunk_ids": []})
        return {"chunk_ids": []}

    with open(LOCAL_IDS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        # ensure it's a dict with 'chunk_ids' key
        if isinstance(data, dict) and "chunk_ids" in data:
            return data
        else:
            return {"chunk_ids": []}

def save_uploaded_ids(data):
    with open(LOCAL_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

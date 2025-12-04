"""
Load trained fetal health model
"""

import pickle
from pathlib import Path


def load_model(model_path):
    """
    Load the trained model
    
    Parameters:
    -----------
    model_path : str
        Path to the model pickle file
    
    Returns:
    --------
    model: Trained prediction model
    """
    
    model_path = Path(model_path)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load model
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    return model
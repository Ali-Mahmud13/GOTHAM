"""
Universal model loader with automatic compatibility fixing
"""

import pickle
import os
import joblib
from pathlib import Path


def load_gdp_model(model_path):
    """
    Universal model loader that handles various pickle compatibility issues
    
    Parameters:
    -----------
    model_path : str or Path
        Path to the model pickle file
    
    Returns:
    --------
    model
        Loaded scikit-learn model
    """
    
    # Convert to Path object for better handling
    model_path = Path(model_path)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Convert back to string for compatibility with older functions
    model_path_str = str(model_path)
    
    # Method 1: Try standard pickle
    try:
        with open(model_path_str, 'rb') as f:
            model = pickle.load(f)
        return model
    except:
        pass
    
    # Method 2: Try with latin1 encoding
    try:
        with open(model_path_str, 'rb') as f:
            model = pickle.load(f, encoding='latin1')
        return model
    except:
        pass
    
    # Method 3: Try with custom unpickler for sklearn compatibility
    try:
        class CompatUnpickler(pickle.Unpickler):
            def find_class(self, module, name):
                # Handle sklearn module renames
                if module == "sklearn.neural_network._multilayer_perceptron":
                    module = "sklearn.neural_network"
                
                # Handle numpy module renames
                if module == "numpy.core.multiarray":
                    module = "numpy"
                if module.startswith("numpy.core"):
                    module = "numpy._core" + module[10:]
                
                # Handle joblib numpy pickle
                if module == "joblib.numpy_pickle":
                    import joblib.numpy_pickle
                    return getattr(joblib.numpy_pickle, name)
                
                return super().find_class(module, name)
        
        with open(model_path_str, 'rb') as f:
            model = CompatUnpickler(f).load()
        return model
    except:
        pass
    
    # Method 4: Try joblib
    try:
        model = joblib.load(model_path_str)
        return model
    except:
        pass
    
    # If all methods fail
    raise Exception(
        f"Unable to load model from {model_path}. "
        "The model may have been created with an incompatible Python/scikit-learn version. "
        "Please re-train and save the model with your current environment, or contact the model creator."
    )
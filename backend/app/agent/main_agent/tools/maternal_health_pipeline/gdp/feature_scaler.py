#!/usr/bin/env python3
"""
Feature scaling configuration for GDP model
"""

import numpy as np

# Define the ranges used for normalization during model training
# These should match the ranges used when the model was originally trained
FEATURE_RANGES = {
    'Age': {'min': 18, 'max': 50},
    'BMI': {'min': 15, 'max': 50},
    'Dia BP': {'min': 40, 'max': 100},
    'HDL': {'min': 20, 'max': 100},
    'Hemoglobin': {'min': 8, 'max': 18},
    'No of Pregnancy': {'min': 0, 'max': 15},
    'OGTT': {'min': 70, 'max': 200},
    'Sys BP': {'min': 80, 'max': 200},
    'Gestation in previous Pregnancy': {'min': 0, 'max': 42},
    'Family History': {'min': 0, 'max': 1},
    'unexplained prenetal loss': {'min': 0, 'max': 1},
    'Large Child or Birth Default': {'min': 0, 'max': 1},
    'PCOS': {'min': 0, 'max': 1},
    'Sedentary Lifestyle': {'min': 0, 'max': 1},
    'Prediabetes': {'min': 0, 'max': 1}
}


def normalize_features(input_df):
    """
    Normalize input features to 0-1 range based on expected ranges
    
    Parameters:
    -----------
    input_df : pandas.DataFrame
        DataFrame with raw feature values
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with normalized feature values (0-1 range)
    """
    normalized_df = input_df.copy()
    
    for feature in input_df.columns:
        if feature in FEATURE_RANGES:
            min_val = FEATURE_RANGES[feature]['min']
            max_val = FEATURE_RANGES[feature]['max']
            
            # Min-max normalization: (x - min) / (max - min)
            normalized_df[feature] = (input_df[feature] - min_val) / (max_val - min_val)
            
            # Clip values to [0, 1] range in case input is outside expected range
            normalized_df[feature] = normalized_df[feature].clip(0, 1)
    
    return normalized_df


def denormalize_features(normalized_df):
    """
    Convert normalized features back to original scale
    
    Parameters:
    -----------
    normalized_df : pandas.DataFrame
        DataFrame with normalized feature values (0-1 range)
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with denormalized feature values
    """
    denormalized_df = normalized_df.copy()
    
    for feature in normalized_df.columns:
        if feature in FEATURE_RANGES:
            min_val = FEATURE_RANGES[feature]['min']
            max_val = FEATURE_RANGES[feature]['max']
            
            # Reverse normalization: x * (max - min) + min
            denormalized_df[feature] = normalized_df[feature] * (max_val - min_val) + min_val
    
    return denormalized_df
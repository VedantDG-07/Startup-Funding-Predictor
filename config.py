"""
Configuration settings for Startup Funding Predictor.
"""
import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models_saved")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

import logging
import os

# Set up central logger for the ETL package
logger = logging.getLogger("StartupIQ-ETL")
logger.setLevel(logging.INFO)

# Avoid adding multiple handlers if logger is already configured
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(log_dir, "etl_pipeline.log"))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

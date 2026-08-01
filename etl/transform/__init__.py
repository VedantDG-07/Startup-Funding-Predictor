from typing import List, Dict, Any
from etl.logger import logger
from etl.transform.cleaner import DataCleaner
from etl.transform.normalizer import DataNormalizer
from etl.transform.feature_engineering import FeatureEngineer
from etl.transform.text_preprocessing import TextPreprocessor

class TransformOrchestrator:
    """
    Coordinates Data Cleaning, Normalization, Feature Engineering, and Text Preprocessing in order.
    """
    def __init__(self):
        self.cleaner = DataCleaner()
        self.normalizer = DataNormalizer()
        self.feature_engineer = FeatureEngineer()
        self.text_preprocessor = TextPreprocessor()

    def transform(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not raw_records:
            logger.warning("No records passed to transform phase.")
            return []
            
        logger.info(f"Starting transformation phase on {len(raw_records)} records...")
        
        # 1. Clean data
        cleaned = self.cleaner.clean_records(raw_records)
        
        # 2. Normalize fields
        normalized = self.normalizer.normalize_records(cleaned)
        
        # 3. Feature engineering
        engineered = self.feature_engineer.engineer_features(normalized)
        
        # 4. Text preprocessing
        final_transformed = self.text_preprocessor.preprocess_text(engineered)
        
        logger.info(f"Transformation complete. Prepared {len(final_transformed)} records.")
        return final_transformed

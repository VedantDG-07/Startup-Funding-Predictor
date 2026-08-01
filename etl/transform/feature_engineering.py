import math
from datetime import datetime
from typing import Dict, Any, List

class FeatureEngineer:
    """
    Computes age, annual funding velocity, and log variables.
    """
    def __init__(self):
        self.current_year = datetime.now().year

    def engineer_features(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        featured_records = []
        for r in records:
            featured = r.copy()
            
            # Years active
            f_year = featured.get("founding_year", 2018)
            years_active = self.current_year - f_year
            years_active = max(years_active, 1)
            featured["years_active"] = years_active
            
            # Funding per round
            rounds = featured.get("funding_rounds_count", 0)
            total_funding = featured.get("total_funding_usd", 0.0)
            featured["funding_per_round"] = total_funding / rounds if rounds > 0 else 0.0
            
            # Funding velocity
            featured["annual_funding_velocity"] = total_funding / years_active
            
            # Log transform
            featured["log_total_funding"] = math.log1p(total_funding)
            
            featured_records.append(featured)
            
        return featured_records

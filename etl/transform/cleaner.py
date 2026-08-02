from typing import Dict, Any, List

class DataCleaner:
    """
    Handles null imputation and type casting for incoming startup dictionaries.
    """
    def clean_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned_records = []
        for r in records:
            cleaned = r.copy()
            
            # Impute missing string fields
            cleaned["name"] = str(cleaned.get("name") or "Unknown Startup").strip()
            cleaned["legal_name"] = str(cleaned.get("legal_name") or cleaned["name"]).strip()
            cleaned["domain"] = str(cleaned.get("domain") or "").strip()
            cleaned["industry"] = str(cleaned.get("industry") or "Technology").strip()
            cleaned["sub_industry"] = str(cleaned.get("sub_industry") or "General").strip()
            cleaned["country"] = str(cleaned.get("country") or "Unknown").strip()
            cleaned["state"] = str(cleaned.get("state") or "Unknown").strip()
            cleaned["city"] = str(cleaned.get("city") or "Unknown").strip()
            cleaned["short_description"] = str(cleaned.get("short_description") or "").strip()
            cleaned["long_description"] = str(cleaned.get("long_description") or cleaned["short_description"]).strip()
            cleaned["employee_count_range"] = str(cleaned.get("employee_count_range") or "1-10").strip()
            
            # Impute and coerce numeric fields
            try:
                cleaned["founding_year"] = int(cleaned.get("founding_year") or 2018)
            except (ValueError, TypeError):
                cleaned["founding_year"] = 2018
                
            try:
                cleaned["total_funding_usd"] = float(cleaned.get("total_funding_usd") or 0.0)
            except (ValueError, TypeError):
                cleaned["total_funding_usd"] = 0.0
                
            try:
                cleaned["funding_rounds_count"] = int(cleaned.get("funding_rounds_count") or 0)
            except (ValueError, TypeError):
                cleaned["funding_rounds_count"] = 0
                
            # Coerce operating status
            status = str(cleaned.get("operating_status") or "operating").lower()
            if status not in ["operating", "acquired", "closed", "ipo"]:
                status = "operating"
            cleaned["operating_status"] = status
            
            # Active flag
            cleaned["is_active"] = bool(cleaned.get("is_active", status == "operating"))
            
            cleaned_records.append(cleaned)
            
        return cleaned_records

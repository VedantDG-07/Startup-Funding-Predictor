import re
from typing import Dict, Any, List

class DataNormalizer:
    """
    Standardizes name representations, URL formats, and currency columns.
    """
    @staticmethod
    def normalize_domain(url: str) -> str:
        """
        Normalize website URLs to base domains (e.g., https://www.google.com/search -> google.com)
        """
        if not url:
            return ""
        domain = url.lower().strip()
        # Remove schemes
        domain = re.sub(r"^https?://(www\.)?", "", domain)
        # Remove path
        domain = domain.split("/")[0]
        return domain

    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normalize names to clean lowercased representations.
        """
        if not name:
            return ""
        # Remove extra whitespaces, lower, strip common legal designations
        name = name.lower().strip()
        name = re.sub(r"\s+", " ", name)
        name = re.sub(r"\b(inc|corp|ltd|co|llc|gmbh|corporation|incorporated|limited)\b\.?", "", name)
        return name.strip()

    def normalize_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized_records = []
        for r in records:
            normalized = r.copy()
            
            # Domain normalization
            normalized["normalized_domain"] = self.normalize_domain(normalized.get("domain", ""))
            
            # Name normalization for duplicate checking
            normalized["normalized_name"] = self.normalize_name(normalized.get("name", ""))
            
            # Format display names
            if normalized["name"]:
                normalized["name"] = normalized["name"].strip()
                
            normalized_records.append(normalized)
            
        return normalized_records

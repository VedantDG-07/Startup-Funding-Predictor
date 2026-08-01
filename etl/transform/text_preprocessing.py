import re
from typing import Dict, Any, List

class TextPreprocessor:
    """
    Cleans raw descriptions and standardizes textual representations.
    """
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        # Remove special characters
        text = re.sub(r"[^\w\s]", " ", text)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def preprocess_text(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed_records = []
        for r in records:
            processed = r.copy()
            
            # Clean description text
            short_desc = processed.get("short_description", "")
            long_desc = processed.get("long_description", "")
            
            processed["cleaned_short_description"] = self.clean_text(short_desc)
            processed["cleaned_long_description"] = self.clean_text(long_desc)
            
            processed_records.append(processed)
            
        return processed_records

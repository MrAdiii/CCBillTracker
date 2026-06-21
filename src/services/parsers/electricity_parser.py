import re
from .base_parser import BaseParser

class ElectricityParser(BaseParser):
    def get_amount_due(self, body, subject):
        match = re.search(r'(?:₹|Rs\.?)\s*([\d,\.]+)', body, re.IGNORECASE)
        if match:
            return f"₹ {match.group(1).strip()}"
        return ""

    def get_due_date(self, body, subject):
        match = re.search(r'due\s+on\s+(\d{1,2}\s+[a-zA-Z]{3}\s+\d{4})', body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def get_bill_identifier(self, body, subject):
        # E.g. "USC No. 108133239"
        match = re.search(r'(?:USC\s+No\.|Consumer\s+No\.|Account\s+No\.)\s*(\d+)', body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

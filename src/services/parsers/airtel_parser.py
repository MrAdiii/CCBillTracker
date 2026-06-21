import re
from .base_parser import BaseParser

class AirtelWifiParser(BaseParser):
    def get_amount_due(self, body, subject):
        match = re.search(r'TOTAL\s+AMOUNT\s*(?:₹|Rs\.?)\s*([\d,\.]+)', body, re.IGNORECASE)
        if match:
            return f"₹ {match.group(1).strip()}"
        return ""

    def get_due_date(self, body, subject):
        match = re.search(r'Due\s+on\s+(\d{1,2}\s+[a-zA-Z]{3}\s+\d{4})', body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def get_bill_identifier(self, body, subject):
        match = re.search(r'Airtel\s+Wi-Fi\s+(\S+)', subject, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""


class AirtelPostpaidParser(BaseParser):
    def get_amount_due(self, body, subject):
        match = re.search(r'TOTAL\s+AMOUNT\s*(?:₹|Rs\.?)\s*([\d,\.]+)', body, re.IGNORECASE)
        if match:
            return f"₹ {match.group(1).strip()}"
        return ""

    def get_due_date(self, body, subject):
        match = re.search(r'Due\s+on\s+(\d{1,2}\s+[a-zA-Z]{3}\s+\d{4})', body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def get_bill_identifier(self, body, subject):
        match = re.search(r'Mobile\s+(\S+)', subject, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

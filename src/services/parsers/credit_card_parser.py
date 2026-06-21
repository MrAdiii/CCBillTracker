import re
from .base_parser import BaseParser

class CreditCardParser(BaseParser):
    
    def get_amount_due(self, body, subject):
        # Commonly "Total Amount Due: Rs. 15,000.00"
        match = re.search(r'total\s+amount(?:.*?)?(?:rs\.?|inr|₹)\s*([\d,\.]+)', body, re.IGNORECASE)
        if match:
            return f"₹ {match.group(1).strip()}"
            
        # Fallback
        match = re.search(r'(?:rs\.?|inr|₹)\s*([\d,\.]+)', body, re.IGNORECASE)
        if match:
            return f"₹ {match.group(1).strip()}"
        return ""

    def get_due_date(self, body, subject):
        # Patterns: "Payment Due Date: 25-Jun-26" or "due date is 25/06/2026"
        keywords = [
            r'payment\s+due\s+date',
            r'due\s+date',
            r'payment\s+due'
        ]
        
        date_numeric = r'\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b'
        date_alpha = r'\b\d{1,2}[-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]\d{2,4}\b'
        date_alpha_reverse = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{1,2},?\s\d{2,4}\b'
        
        for kw in keywords:
            pattern = re.compile(rf'{kw}.{{0,120}}?({date_numeric}|{date_alpha}|{date_alpha_reverse})', re.IGNORECASE)
            match = pattern.search(body)
            if match:
                return match.group(1).strip()
        return ""

    def get_bill_identifier(self, body, subject):
        # Looking for "Card ending in 1234" or "XX1234"
        match = re.search(r'(?:ending\s+(?:in|with)\s+|card\s*(?:no\.?)?\s*(?:x{2,6}|x{2,4}-x{4}-x{4}-|[*]{2,6}))(\d{4})', body, re.IGNORECASE)
        if match:
            return f"Card ending {match.group(1)}"
        return ""

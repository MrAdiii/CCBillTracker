import re
from .base_parser import BaseParser

class CreditCardParser(BaseParser):
    
    def format_amount(self, val):
        val = val.strip()
        is_credit = False
        if 'cr' in val.lower() or val.startswith('-'):
            is_credit = True
            
        clean_num = re.sub(r'[^\d,\.]', '', val).strip()
        clean_num = clean_num.strip('.,')
        
        if is_credit:
            return f"-₹ {clean_num}"
        else:
            return f"₹ {clean_num}"

    def get_amount_due(self, body, subject):
        # 1. Match Axis Bank tabular format first
        axis_pattern = r'Total\s+Amount\s+Due\s+INR\s+Minimum\s+Amount\s+Due\s+\(INR\)\s+Payment\s+Due\s+Date\s+\(DD-MM-YYYY\)\s+([\d,\.]+\s*(?:Cr|Dr)?)'
        match = re.search(axis_pattern, body, re.IGNORECASE)
        if match:
            return self.format_amount(match.group(1))

        # 2. General "Total Amount Due" patterns with currency
        total_patterns = [
            r'total\s+amount\s+due[\s\S]{0,100}?(?:rs\.?|inr|₹)\s*(-?[\d,\.]+(?:\s*(?:cr|dr))?)',
            r'total\s+amount[\s\S]{0,100}?(?:rs\.?|inr|₹)\s*(-?[\d,\.]+(?:\s*(?:cr|dr))?)',
            r'amount\s+due[\s\S]{0,100}?(?:rs\.?|inr|₹)\s*(-?[\d,\.]+(?:\s*(?:cr|dr))?)',
        ]
        for pattern in total_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return self.format_amount(match.group(1))

        # 3. Fallback with context safety check (avoid matching promotional offers)
        for match in re.finditer(r'(?:rs\.?|inr|₹)\s*(-?[\d,\.]+(?:\s*(?:cr|dr))?)', body, re.IGNORECASE):
            val = match.group(1)
            start = match.start()
            context = body[max(0, start-30):start].lower()
            if 'above' not in context and 'greater' not in context and 'convert' not in context:
                return self.format_amount(val)
                
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

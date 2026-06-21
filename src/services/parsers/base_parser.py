import re
from datetime import datetime

class BaseParser:
    def __init__(self, provider_config):
        self.provider_config = provider_config
        self.biller_name = provider_config.get('name', 'Unknown')
        self.bill_type = provider_config.get('type', 'Unknown')

    def extract_email_body(self, msg):
        body = ""
        if msg.is_multipart():
            plain_parts = []
            html_parts = []
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" not in content_disposition:
                    if content_type == "text/plain":
                        plain_parts.append(part)
                    elif content_type == "text/html":
                        html_parts.append(part)
            
            parts_to_use = plain_parts if plain_parts else html_parts
            for part in parts_to_use:
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    body += part.get_payload(decode=True).decode(charset, errors='ignore')
                except:
                    pass
        else:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='ignore')
            except:
                pass
        return body

    def clean_text(self, text):
        return re.sub(r'\s+', ' ', text).strip()

    def normalize_date(self, raw_date):
        if not raw_date:
            return ""
        raw_date = raw_date.strip()
        for fmt in ("%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y", "%b %d, %Y", "%B %d, %Y", "%d-%b-%y", "%d/%m/%y", "%d-%m-%y"):
            try:
                dt = datetime.strptime(raw_date, fmt)
                return dt.strftime("%d-%b-%Y")
            except ValueError:
                pass
        return raw_date

    def extract(self, msg, subject=""):
        body = self.clean_text(self.extract_email_body(msg))
        
        raw_due_date = self.get_due_date(body, subject)
        
        return {
            "amount_due": self.get_amount_due(body, subject),
            "due_date": self.normalize_date(raw_due_date),
            "bill_identifier": self.get_bill_identifier(body, subject),
            "biller_name": self.biller_name,
            "bill_type": self.bill_type
        }

    def get_amount_due(self, body, subject):
        return ""
    
    def get_due_date(self, body, subject):
        return ""
        
    def get_bill_identifier(self, body, subject):
        return ""

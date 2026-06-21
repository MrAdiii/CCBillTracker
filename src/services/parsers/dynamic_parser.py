import re
from datetime import datetime

class DynamicParser:
    def __init__(self, provider_config, global_config):
        self.provider_config = provider_config
        self.global_config = global_config
        self.biller_name = provider_config.get('name', 'Unknown')
        self.bill_type = provider_config.get('type', 'Unknown')
        
        self.extraction_rules = provider_config.get('extraction_rules', {})

        # Exclusions
        self.amount_exclude = global_config.get('amount_exclude', [])


    def clean_text(self, text):
        import html
        # Unescape HTML entities (e.g. &nbsp;, &#8377;)
        text = html.unescape(text)
        # Strip all HTML tags, replacing them with a space
        text = re.sub(r'<[^>]+>', ' ', text)
        # Replace multiple spaces and newlines with a single space
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
            
            # Prefer HTML since banks often leave text/plain empty or use it for "Please enable HTML"
            parts_to_use = html_parts if html_parts else plain_parts
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

    def extract(self, msg, subject=""):
        body = self.clean_text(self.extract_email_body(msg))
        
        extracted_data = {}
        
        for field, patterns in self.extraction_rules.items():
            if not isinstance(patterns, list):
                patterns = [patterns]
                
            match_found = False
            for pattern in patterns:
                # If field is amount_due, apply safety exclusions
                if field == 'amount_due':
                    for match in re.finditer(pattern, body):
                        val = match.group(1)
                        start = match.start()
                        context = body[max(0, start-30):start].lower()
                        
                        is_safe = True
                        for exclude_kw in self.amount_exclude:
                            if exclude_kw.lower() in context:
                                is_safe = False
                                break
                                
                        if is_safe:
                            extracted_data[field] = val
                            match_found = True
                            break
                    if match_found:
                        break
                else:
                    match = re.search(pattern, body)
                    # Try searching subject if not found in body
                    if not match and subject:
                        match = re.search(pattern, subject)
                        
                    if match:
                        extracted_data[field] = match.group(1).strip()
                        break
        
        # Apply formatting based on schema
        sheet_schema = self.global_config.get('sheet_schema', [])
        for col in sheet_schema:
            col_id = col['id']
            col_type = col.get('type', 'string')
            
            # Prioritize statically defined field in the provider config
            if col_id in self.provider_config and isinstance(self.provider_config[col_id], (str, int, float)):
                val = str(self.provider_config[col_id])
                extracted_data[col_id] = val
            else:
                val = extracted_data.get(col_id, "")
            
            if val:
                if col_type == 'amount':
                    extracted_data[col_id] = self.format_amount(val)
                elif col_type == 'date':
                    extracted_data[col_id] = self.normalize_date(val)
                    
        # Inject standard fields
        extracted_data['biller_name'] = self.biller_name
        extracted_data['bill_type'] = self.bill_type
        
        return extracted_data

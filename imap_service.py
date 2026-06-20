import imaplib
import email
import os
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime
import tempfile
import re
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')
try:
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
        PROVIDERS = config.get('providers', [])
except Exception as e:
    print(f"Failed to load config.yaml: {e}")
    PROVIDERS = []

# Regex patterns for due date extraction (searched in order, first match wins)
DUE_DATE_PATTERNS = [
    # "Payment due date" followed by DD/MM/YYYY or DD-MM-YYYY (handles Axis tabular, YES Bank tab-separated)
    r"payment\s*due\s*date[\s\S]{0,120}?(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
    # "Payment due date" followed by DD-Mon-YYYY (SBI style)
    r"payment\s*due\s*date[\s\S]{0,120}?(\d{1,2}-[A-Za-z]{3,9}-\d{4})",
    # "Payment due by/on Month DD, YYYY" (ICICI style, may span newlines)
    r"payment\s+due\s*[\n\r]*\s*by\s+([A-Za-z]+\s+\d{1,2},?\s*\d{4})",
    # Generic "due date" + DD/MM/YYYY or DD-MM-YYYY
    r"due\s+date[\s:]+?(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
    # Generic "due date" + DD-Mon-YYYY
    r"due\s+date[\s:]+?(\d{1,2}-[A-Za-z]{3,9}-\d{4})",
    # "due by/on" + Month DD, YYYY
    r"due\s+(?:by|on)\s+([A-Za-z]+\s+\d{1,2},?\s*\d{4})",
]

# Date formats to try when normalizing extracted date strings to DD-MMM-YYYY
NORMALIZE_DATE_FORMATS = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d-%b-%Y",
    "%d-%B-%Y",
    "%B %d, %Y",
    "%B %d %Y",
    "%d %B %Y",
    "%d %b %Y",
    "%b %d, %Y",
    "%b %d %Y",
]

def clean(text):
    # clean text for creating a file
    return "".join(c if c.isalnum() else "_" for c in text)

class ImapService:
    def __init__(self, email_account, app_password, unprocessed_label="Unprocessed", processed_label="Processed"):
        self.email_account = email_account
        self.app_password = app_password
        self.unprocessed_label = unprocessed_label
        self.processed_label = processed_label
        self.mail = None

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com")
            self.mail.login(self.email_account, self.app_password)
            print("Successfully authenticated via IMAP.")
        except Exception as e:
            print(f"Failed to connect to IMAP: {e}")
            raise e

    def fetch_unprocessed_statements(self):
        """
        Fetches emails from the configured unprocessed label/mailbox.
        Returns a list of dicts with email info and path to downloaded PDF.
        """
        try:
            status, messages = self.mail.select(f'\"{self.unprocessed_label}\"')
            if status != "OK":
                print(f"Could not select '{self.unprocessed_label}' mailbox. Please ensure the label exists.")
                return []
        except Exception as e:
             print(f"Error selecting mailbox: {e}")
             return []

        status, response = self.mail.uid('SEARCH', None, "ALL")
        if status != "OK":
            print("No emails found.")
            return []

        messages = response[0].split()
        extracted_data = []

        for msg_id in messages:
            try:
                status, msg_data = self.mail.uid('FETCH', msg_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        
                        sender = msg.get("From")
                        date_str = msg.get("Date")
                        
                        try:
                            if date_str:
                                dt = parsedate_to_datetime(date_str)
                                date_str = dt.strftime("%d-%b-%Y")
                        except Exception as e:
                            print(f"Date parsing failed for {date_str}: {e}")

                        # Extract body once for reuse
                        body = self._get_email_body(msg)
                        combined_text = f"{subject}\n{body}"

                        provider_name, provider_type = self.identify_provider(sender, body, subject)

                        if not provider_name:
                            print(f"Could not identify provider for email: {subject}")
                            continue
                        
                        # Extract due date from subject + body
                        due_date = self.extract_due_date(combined_text)
                        
                        # Best-effort extraction of financial summary
                        financial_data = self.extract_financial_summary(combined_text)
                            
                        pdf_path = self.extract_pdf(msg)
                        
                        if not pdf_path and provider_type == 'Credit Card':
                            print(f"No PDF found for Credit Card email: {subject}. Skipping.")
                            continue
                            
                        extracted_data.append({
                            'msg_id': msg_id,
                            'subject': subject,
                            'date': date_str,
                            'due_date': due_date,
                            'biller_name': provider_name,
                            'bill_type': provider_type,
                            'pdf_path': pdf_path,
                            'total_amount_due': financial_data.get('total_amount_due', 'N/A'),
                            'min_amount_due': financial_data.get('min_amount_due', 'N/A'),
                        })
                            
            except Exception as e:
                print(f"Error processing message {msg_id}: {e}")

        return extracted_data

    def _get_email_body(self, msg):
        """Extracts the plain text body from an email message.
        Falls back to stripping HTML tags if no plain text part is found."""
        body = ""
        html_body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" in content_disposition:
                    continue
                if content_type == "text/plain":
                    try:
                        body += part.get_payload(decode=True).decode(errors='replace')
                    except:
                        pass
                elif content_type == "text/html":
                    try:
                        html_body = part.get_payload(decode=True).decode(errors='replace')
                    except:
                        pass
        else:
            try:
                if msg.get_content_type() == "text/html":
                    html_body = msg.get_payload(decode=True).decode(errors='replace')
                else:
                    body = msg.get_payload(decode=True).decode(errors='replace')
            except:
                pass
        
        # Prefer plain text, fall back to stripped HTML
        if not body and html_body:
            body = re.sub(r'<[^>]+>', ' ', html_body)
            body = re.sub(r'&nbsp;', ' ', body)
            body = re.sub(r'\s+', ' ', body)
        
        return body

    def _normalize_date_str(self, date_str):
        """Attempts to normalize a date string to DD-MMM-YYYY format."""
        date_str = date_str.strip().rstrip('.')
        for fmt in NORMALIZE_DATE_FORMATS:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%d-%b-%Y")
            except ValueError:
                continue
        return date_str  # Return as-is if no format matches

    def extract_due_date(self, text):
        """Extracts the payment due date from email subject + body text.
        Searches both subject and body against a prioritized list of regex patterns.
        Returns normalized DD-MMM-YYYY string or 'N/A' if not found."""
        for pattern in DUE_DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_date = match.group(1).strip()
                normalized = self._normalize_date_str(raw_date)
                print(f"  Due date extracted: {raw_date} -> {normalized}")
                return normalized
        return "N/A"

    def extract_financial_summary(self, text):
        """Best-effort extraction of financial data from email text.
        Returns a dict with 'total_amount_due' and 'min_amount_due' when found.
        These are stored as raw strings for flexible use downstream."""
        summary = {}
        
        # Total Amount Due
        total_patterns = [
            r"total\s*amount\s*due[\s\S]{0,80}?(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)",
            r"total\s*amount\s*due[\s\S]{0,150}?([\d,]+\.\d{2})",
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1):
                summary['total_amount_due'] = match.group(1).strip()
                break
        
        # Minimum Amount Due
        min_patterns = [
            r"minimum\s*amount\s*due[\s\S]{0,80}?(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)",
            r"minimum\s*amount\s*due[\s\S]{0,150}?([\d,]+\.\d{2})",
        ]
        for pattern in min_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1):
                summary['min_amount_due'] = match.group(1).strip()
                break
        
        return summary

    def identify_provider(self, sender, body, subject):
        """Identifies the provider from the sender address, subject, or body."""
        sender_lower = str(sender).lower()
        subject_lower = str(subject).lower() if subject else ""
        body_lower = str(body).lower() if body else ""
        
        for provider in PROVIDERS:
            for domain in provider.get('domains', []):
                if domain.lower() in sender_lower:
                    keywords = provider.get('subject_keywords', [])
                    if keywords:
                        if any(kw.lower() in subject_lower for kw in keywords):
                            return provider['name'], provider.get('type', 'Unknown')
                    else:
                        return provider['name'], provider.get('type', 'Unknown')

        if subject and ("fwd" in subject_lower or "fw:" in subject_lower):
            for provider in PROVIDERS:
                for domain in provider.get('domains', []):
                    if domain.lower() in body_lower:
                        keywords = provider.get('subject_keywords', [])
                        if keywords:
                            if any(kw.lower() in subject_lower or kw.lower() in body_lower for kw in keywords):
                                return provider['name'], provider.get('type', 'Unknown')
                        else:
                            return provider['name'], provider.get('type', 'Unknown')
                     
        return None, None

    def extract_pdf(self, msg):
        if not msg.is_multipart():
            return None

        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    try:
                        filename, encoding = decode_header(filename)[0]
                        if isinstance(filename, bytes):
                            filename = filename.decode(encoding if encoding else "utf-8")
                    except:
                        pass
                    
                    if filename.lower().endswith('.pdf'):
                        temp_dir = tempfile.gettempdir()
                        filepath = os.path.join(temp_dir, clean(filename) + ".pdf")
                        
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        return filepath
        return None

    def move_to_processed(self, msg_id):
        try:
            result = self.mail.uid('COPY', msg_id, f'\"{self.processed_label}\"')
            if result[0] == 'OK':
                self.mail.uid('STORE', msg_id, '+FLAGS', '(\\Deleted)')
                self.mail.expunge()
                print(f"Moved message {msg_id} to '{self.processed_label}' label.")
            else:
                print(f"Failed to copy message {msg_id} to '{self.processed_label}'.")
        except Exception as e:
            print(f"Error moving message {msg_id}: {e}")

    def close(self):
        try:
            self.mail.close()
            self.mail.logout()
        except:
            pass

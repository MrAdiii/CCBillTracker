import imaplib
import email
import os
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime
import tempfile
import re
import yaml
import urllib.parse
from .parsers.parser_factory import ParserFactory

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config.yaml')
try:
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
        PROVIDERS = config.get('providers', [])
except Exception as e:
    print(f"Failed to load config.yaml: {e}")
    PROVIDERS = []

def clean(text):
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
                status, msg_data = self.mail.uid('FETCH', msg_id, "(X-GM-THRID RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        meta_str = response_part[0].decode(errors='ignore')
                        thrid_match = re.search(r'X-GM-THRID (\d+)', meta_str)
                        
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        
                        sender = msg.get("From")
                        date_str = msg.get("Date")
                        msg_id_header = msg.get("Message-ID", "")
                        
                        try:
                            if date_str:
                                dt = parsedate_to_datetime(date_str)
                                date_str = dt.strftime("%d-%b-%Y")
                        except Exception as e:
                            print(f"Date parsing failed for {date_str}: {e}")

                        # To identify forwarded providers, we pass the raw msg string body safely if needed
                        # But typically sender and subject are enough
                        provider_config = self.identify_provider(sender, subject, "")
                        
                        if not provider_config:
                            # try checking body for forwards
                            raw_body = self._get_email_body(msg)
                            provider_config = self.identify_provider(sender, subject, raw_body)

                        if not provider_config:
                            print(f"Could not identify provider for email: {subject}")
                            continue
                        
                        parser = ParserFactory.get_parser(provider_config, config)
                        parsed_data = parser.extract(msg, subject)
                        
                        pdf_path = self.extract_pdf(msg)
                        if not pdf_path and provider_config.get('type') == 'Credit Card':
                            print(f"No PDF found for Credit Card email: {subject}. Skipping.")
                            continue
                            
                        email_link = ""
                        if thrid_match:
                            thrid_decimal = int(thrid_match.group(1))
                            thrid_hex = hex(thrid_decimal)[2:]
                            email_link = f"https://mail.google.com/mail/u/0/#all/{thrid_hex}"
                        elif msg_id_header:
                            email_link = f"https://mail.google.com/mail/u/0/#search/rfc822msgid%3A{urllib.parse.quote(msg_id_header)}"
                        
                        # System fields to mix with parsed data
                        record = {
                            'msg_id': msg_id,
                            'subject': subject,
                            'date': date_str,
                            'pdf_path': pdf_path,
                            'email_link': email_link,
                            'file_naming_pattern': provider_config.get('file_naming_pattern')
                        }
                        # Merge the dynamically parsed fields directly into the record
                        record.update(parsed_data)
                        
                        extracted_data.append(record)
                            
            except Exception as e:
                print(f"Error processing message {msg_id}: {e}")

        return extracted_data

    def _get_email_body(self, msg):
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
        if not body and html_body:
            import re
            body = re.sub(r'<[^>]+>', ' ', html_body)
            body = re.sub(r'&nbsp;', ' ', body)
            body = re.sub(r'\s+', ' ', body)
        return body

    def identify_provider(self, sender, subject, body):
        sender_lower = str(sender).lower()
        subject_lower = str(subject).lower() if subject else ""
        body_lower = str(body).lower() if body else ""
        
        # 1. Match by sender domain first (most specific)
        for provider in PROVIDERS:
            for domain in provider.get('domains', []):
                if domain.lower() in sender_lower:
                    req_keywords = provider.get('required_keywords', [])
                    req_match = True
                    if req_keywords:
                        req_match = all(rkw.lower() in subject_lower for rkw in req_keywords)
                    
                    if req_match:
                        keywords = provider.get('matching_keywords', [])
                        if keywords:
                            if any(kw.lower() in subject_lower for kw in keywords):
                                return provider
                        else:
                            return provider

        if subject and ("fwd" in subject_lower or "fw:" in subject_lower):
            for provider in PROVIDERS:
                for domain in provider.get('domains', []):
                    if domain.lower() in body_lower:
                        req_keywords = provider.get('required_keywords', [])
                        req_match = True
                        if req_keywords:
                            req_match = all(rkw.lower() in subject_lower or rkw.lower() in body_lower for rkw in req_keywords)
                        
                        if req_match:
                            keywords = provider.get('matching_keywords', [])
                            if keywords:
                                if any(kw.lower() in subject_lower or kw.lower() in body_lower for kw in keywords):
                                    return provider
                            else:
                                return provider
                     
        return None

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

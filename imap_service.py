import imaplib
import email
import os
from email.header import decode_header
import tempfile
import re

# Target Banks list as per requirements
TARGET_BANKS = [
    'Emailstatements.cards@hdfcbank.bank.in', 
    'EmailStatements.cards@hdfcbank.net', 
    'cc.statements@axis.bank.in', 
    'cc.statements@axisbank.com', 
    'credit_cards@icici.bank.in', 
    'credit_cards@icicibank.com', 
    'estatements@icicibank.com', 
    'creditcard.estatements@indusind.com', 
    'estatements@indusind.com', 
    'statements@sbicard.com', 
    'prime.card@sbicard.com', 
    'ELITE.card@sbicard.com', 
    'aurumcardstatement@sbicard.com', 
    'estatement@yesbank.in'
]

def clean(text):
    # clean text for creating a file
    return "".join(c if c.isalnum() else "_" for c in text)

class ImapService:
    def __init__(self, email_account, app_password):
        self.email_account = email_account
        self.app_password = app_password
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
        Fetches emails from the 'Unprocessed' label/mailbox.
        Returns a list of dicts with email info and path to downloaded PDF.
        """
        try:
            status, messages = self.mail.select("Unprocessed")
            if status != "OK":
                print("Could not select 'Unprocessed' mailbox. Please ensure the label exists.")
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

                        bank_name = self.extract_bank_name(sender, msg, subject)

                        if not bank_name:
                            print(f"Could not identify bank for email: {subject}")
                            continue
                            
                        pdf_path = self.extract_pdf(msg)
                        
                        if pdf_path:
                            extracted_data.append({
                                'msg_id': msg_id,
                                'subject': subject,
                                'date': date_str,
                                'bank_name': bank_name,
                                'pdf_path': pdf_path
                            })
                        else:
                            print(f"No PDF found for email: {subject}")
                            
            except Exception as e:
                print(f"Error processing message {msg_id}: {e}")

        return extracted_data

    def extract_bank_name(self, sender, msg, subject):
        sender_lower = str(sender).lower()
        
        for target in TARGET_BANKS:
            if target.lower() in sender_lower:
                return target.split('@')[1].split('.')[0].upper()

        if subject and ("fwd" in subject.lower() or "fw:" in subject.lower()):
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        try:
                            body += part.get_payload(decode=True).decode()
                        except:
                            pass
            else:
                try:
                    body = msg.get_payload(decode=True).decode()
                except:
                    pass
            
            body_lower = body.lower()
            for target in TARGET_BANKS:
                if target.lower() in body_lower:
                     return target.split('@')[1].split('.')[0].upper()
                     
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
            result = self.mail.uid('COPY', msg_id, 'Processed')
            if result[0] == 'OK':
                self.mail.uid('STORE', msg_id, '+FLAGS', '(\\Deleted)')
                self.mail.expunge()
                print(f"Moved message {msg_id} to 'Processed' label.")
            else:
                print(f"Failed to copy message {msg_id} to 'Processed'.")
        except Exception as e:
            print(f"Error moving message {msg_id}: {e}")

    def close(self):
        try:
            self.mail.close()
            self.mail.logout()
        except:
            pass

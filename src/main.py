import os
import time
from dotenv import load_dotenv

from services.google_auth import authenticate
from services.imap_service import ImapService
from services.drive_service import DriveService
from services.sheets_service import SheetsService

def main():
    # Load environment variables from the project root
    project_root = os.path.dirname(os.path.dirname(__file__))
    load_dotenv(os.path.join(project_root, '.env'))

    email_account = os.getenv('EMAIL_ACCOUNT')
    app_password = os.getenv('APP_PASSWORD')
    drive_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    unprocessed_label = os.getenv('EMAIL_UNPROCESSED_LABEL', 'Unprocessed')
    processed_label = os.getenv('EMAIL_PROCESSED_LABEL', 'Processed')
    
    if not all([email_account, app_password, drive_folder_id, sheet_id]):
        print("Missing environment variables. Please check your .env file.")
        return

    print("Authenticating with Google API (Drive and Sheets)...")
    try:
        creds = authenticate()
    except Exception as e:
        print(f"Google API Authentication failed: {e}")
        return

    drive_service = DriveService(creds)
    sheets_service = SheetsService(creds, sheet_id)

    print(f"Connecting to IMAP for {email_account}...")
    imap_service = ImapService(email_account, app_password, unprocessed_label, processed_label)
    try:
        imap_service.connect()
    except Exception as e:
        print("Failed to connect to IMAP. Exiting.")
        return

    print("Fetching unprocessed statements...")
    try:
        statements = imap_service.fetch_unprocessed_statements()
        print(f"Found {len(statements)} unprocessed statements.")
        
        for statement in statements:
            msg_id = statement['msg_id']
            subject = statement['subject']
            date_str = statement['date']
            due_date = statement.get('due_date', '')
            biller_name = statement.get('biller_name', '')
            bill_type = statement.get('bill_type', '')
            bill_identifier = statement.get('bill_identifier', '')
            amount_due = statement.get('amount_due', '')
            pdf_path = statement.get('pdf_path', '')
            email_link = statement.get('email_link', '')
            
            print(f"\nProcessing statement from {biller_name} ({bill_type}) - Subject: {subject}")
            print(f"  ID: {bill_identifier} | Due Date: {due_date} | Amount: {amount_due}")
            
            # Determine Month and Year for the filename
            from datetime import datetime
            month_year = ""
            date_to_use = due_date if due_date and due_date != "N/A" else date_str
            try:
                dt = datetime.strptime(date_to_use, "%d-%b-%Y")
                month_year = dt.strftime("%B %Y")
            except:
                month_year = ""
                
            # Determine the parts for the friendly filename
            if bill_type == 'Credit Card':
                friendly_name_parts = [biller_name, "CC", "Bill", month_year]
            else:
                # For utility bills, include the Biller Name, Bill Type, Bill Identifier, and Month Year
                friendly_name_parts = [biller_name, bill_type, bill_identifier, "Bill", month_year]
                
            friendly_name_parts = [p for p in friendly_name_parts if p and p != "N/A"]
            friendly_name = " ".join(friendly_name_parts).replace("  ", " ").strip() + ".pdf"
            
            # 1. Upload to Drive
            drive_link = None
            if pdf_path:
                print(f"Uploading to Drive as: {friendly_name}...")
                drive_link = drive_service.upload_pdf(pdf_path, drive_folder_id, display_name=friendly_name)
                if not drive_link:
                    print(f"Failed to upload {pdf_path}. Will still log to sheet without link.")
            else:
                print("No PDF to upload for this bill.")
                
            # 2. Append to Sheet
            print("Logging to Google Sheets...")
            result = sheets_service.append_bill_record(date_str, biller_name, bill_type, bill_identifier, amount_due, due_date, drive_link, email_link)
            
            if result:
                # 3. Move email to Processed label
                imap_service.move_to_processed(msg_id)
            else:
                print("Failed to log to sheet. Will not mark email as processed.")
            
            # 4. Cleanup local PDF
            if pdf_path:
                try:
                    os.remove(pdf_path)
                except Exception as e:
                    print(f"Failed to delete local temp file {pdf_path}: {e}")
                
            # Small delay to avoid hitting rate limits
            time.sleep(1)
            
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
    finally:
        print("\nClosing IMAP connection.")
        imap_service.close()

if __name__ == "__main__":
    main()

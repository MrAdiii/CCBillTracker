import os
import time
from dotenv import load_dotenv

from google_auth import authenticate
from imap_service import ImapService
from drive_service import DriveService
from sheets_service import SheetsService

def main():
    # Load environment variables
    load_dotenv()
    
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
            due_date = statement['due_date']
            biller_name = statement['biller_name']
            bill_type = statement['bill_type']
            pdf_path = statement['pdf_path']
            email_link = statement.get('email_link', '')
            total_amount_due = statement.get('total_amount_due', 'N/A')
            min_amount_due = statement.get('min_amount_due', 'N/A')
            
            print(f"\nProcessing statement from {biller_name} ({bill_type}) - Subject: {subject}")
            print(f"  Due Date: {due_date} | Total: {total_amount_due} | Min: {min_amount_due}")
            
            # 1. Upload to Drive
            # 1. Upload to Drive
            drive_link = None
            if pdf_path:
                print("Uploading to Drive...")
                drive_link = drive_service.upload_pdf(pdf_path, drive_folder_id)
                if not drive_link:
                    print(f"Failed to upload {pdf_path}. Will still log to sheet without link.")
            else:
                print("No PDF to upload for this bill.")
                
            # 2. Append to Sheet
            print("Logging to Google Sheets...")
            result = sheets_service.append_bill_record(date_str, due_date, biller_name, bill_type, drive_link, email_link)
            
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

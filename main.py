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
    imap_service = ImapService(email_account, app_password)
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
            bank_name = statement['bank_name']
            pdf_path = statement['pdf_path']
            
            print(f"\nProcessing statement from {bank_name} - Subject: {subject}")
            
            # 1. Upload to Drive
            print("Uploading to Drive...")
            drive_link = drive_service.upload_pdf(pdf_path, drive_folder_id)
            
            if not drive_link:
                print(f"Failed to upload {pdf_path}. Skipping sheet update.")
                # We do not move the email to processed if upload fails, 
                # so it can be retried next time.
                continue
                
            # 2. Append to Sheet
            print("Logging to Google Sheets...")
            result = sheets_service.append_bill_record(date_str, bank_name, drive_link)
            
            if result:
                # 3. Move email to Processed label
                imap_service.move_to_processed(msg_id)
            else:
                print("Failed to log to sheet. Will not mark email as processed.")
            
            # 4. Cleanup local PDF
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

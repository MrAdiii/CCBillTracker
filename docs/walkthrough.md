# CC Bill Tracker Implementation Walkthrough

I have successfully generated the complete codebase for the lightweight, automated Python service that fetches credit card e-statements from Gmail via IMAP, uploads the attached PDFs to Google Drive, and logs the bill details into Google Sheets.

## Changes Made

Based on your architectural updates, the Gmail API has been completely removed in favor of standard IMAP, bypassing Google Cloud verification and the 7-day OAuth token expiration for restricted scopes.

1. **Project Setup**:
   - `requirements.txt`: Includes Google API clients and `python-dotenv`.
   - `.env.example`: Template for environment variables including `EMAIL_ACCOUNT`, `APP_PASSWORD`, `GOOGLE_DRIVE_FOLDER_ID`, and `GOOGLE_SHEET_ID`.
   - `.gitignore`: Safely ignores `token.json`, `credentials.json`, `.env`, etc.
   - `Dockerfile`: Sets up a slim Python 3.11 image to run `main.py`.
   - `.agents/STATUS.md`: Created the agentic file to store the project scope and status for future AI sessions.

2. **Python Services**:
   - `google_auth.py`: Retained only the Drive and Sheets OAuth flow using desktop credentials.
   - `imap_service.py` **[NEW]**: Connects securely to `imap.gmail.com` using the provided app password. Fetches raw email bytes from the "Unprocessed" label, parses subjects/senders/body for bank names and forwarded metadata, extracts PDF attachments to a local temp folder, and uses IMAP `UID COPY` / `STORE` commands to move processed emails to the "Processed" label.
   - `drive_service.py`: Uses Google Drive APIs to upload the PDF into a specified folder and returns a `webViewLink`.
   - `sheets_service.py`: Dynamically computes the current month's sheet name (e.g., `Bills_June_2026`). It guarantees the sheet exists with headers and appends new rows.
   - `main.py`: Orchestrates the flow seamlessly—authenticating Drive/Sheets, connecting to IMAP, and executing the full end-to-end pipeline on each fetched email.

## Setup Instructions

> [!IMPORTANT]
> To run this locally or via Docker, please follow these setup steps:

1. **IMAP Configuration**: 
   - Ensure you have generated a **Google App Password** for the target email account. 
   - Update your `.env` file with `EMAIL_ACCOUNT` and `APP_PASSWORD`.
2. **Google Cloud APIs**:
   - Download your OAuth 2.0 Client ID as `credentials.json` from the Google Cloud Console.
   - Ensure the Drive API and Sheets API are enabled for your project.
3. **Environment Variables**:
   - Update your `.env` file with `GOOGLE_DRIVE_FOLDER_ID` and `GOOGLE_SHEET_ID`.
4. **First Run (OAuth Flow)**:
   - Run `python main.py` locally for the first time. This will trigger a browser window to authenticate with Google Drive and Sheets, generating a `token.json` file.
   - Once `token.json` is created, you can containerize and run the application via Docker securely.

## Labels Note

> [!NOTE]
> The `imap_service.py` connects to the mailbox named `Unprocessed` and moves completed emails to `Processed`. Ensure you have created these labels in your Gmail account, and that you have a filter configured to place incoming statements into the `Unprocessed` label.
